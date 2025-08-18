from __future__ import annotations

from sqlite3 import Cursor

from pypika import Query, Table, functions as fn

from src.schemas import (
    StageCreate,
    StageDetail,
    StagePublic,
    TaskCreate,
    TaskPublic,
    TaskUpdate,
)

schema = """
CREATE TABLE stage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING(30) NOT NULL
);

CREATE TABLE task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    stage_id INT NOT NULL,
    position INT NOT NULL,
    FOREIGN KEY (stage_id) REFERENCES stage(id)
);
"""


class NoFieldsToUpdate(ValueError):
    def __init__(self):
        super().__init__("No fields provided to update")


class NotFound(ValueError):
    def __init__(self, model: str, id: int):
        self.model = model
        self.id = id
        super().__init__(f"{model} with id {id} not found")


class MultipleRowsUpdated(RuntimeError):
    def __init__(self, rowcount: int):
        self.rowcount = rowcount
        super().__init__(f"Unexpectedly updated {rowcount} rows")


Stage_T = Table("stage")
Task_T = Table("task")


def fetch_stages_with_tasks(cur: Cursor) -> list[StageDetail]:
    cur.execute(Stage_T.select("*").get_sql())
    stages = [StagePublic.from_row(row) for row in cur.fetchall()]

    stage_details: list[StageDetail] = []
    for stage in stages:
        cur.execute(Task_T.select("*").where(Task_T.stage_id == stage.id).get_sql())
        stage_details.append(
            StageDetail(
                **stage.model_dump(),
                tasks=[TaskPublic.from_row(row) for row in cur.fetchall()],
            )
        )
    return stage_details


def fetch_all_stages(cur: Cursor) -> list[StagePublic]:
    query = Stage_T.select("*").get_sql()
    return [StagePublic.from_row(res) for res in cur.execute(query).fetchall()]


def fetch_stage_by_name(cur: Cursor, name: str) -> StagePublic | None:
    query = Stage_T.select("*").where(Stage_T.name == name).get_sql()
    row = cur.execute(query).fetchone()
    if not row:
        return None
    return StagePublic.from_row(row)


def fetch_stage_by_id(cur: Cursor, id: int) -> StagePublic | None:
    query = Stage_T.select("*").where(Stage_T.id == id).get_sql()
    row = cur.execute(query).fetchone()
    if not row:
        return None
    return StagePublic.from_row(row)


def fetch_next_task_position(cur: Cursor, stage_id: int) -> int:
    query = (
        Task_T.select(fn.Max(Task_T.position).as_("next_pos"))
        .where(Task_T.stage_id == stage_id)
        .get_sql()
    )
    next_pos = cur.execute(query).fetchone()
    return next_pos[0] + 1 if next_pos[0] is not None else 0


def insert_task(cur: Cursor, task: TaskCreate) -> TaskPublic:
    next_position = fetch_next_task_position(cur, task.stage_id)
    query = (
        Query.into(Task_T)
        .columns("name", "stage_id", "position")
        .insert(task.name, task.stage_id, next_position)
        .get_sql()
    )
    cur = cur.execute(query)

    last_id = cur.lastrowid
    if not last_id:
        raise RuntimeError(f"error inserting row {task} into {Task_T}")
    new_task = fetch_task_by_id(cur, last_id)
    assert new_task is not None
    return new_task


def fetch_all_tasks(cur: Cursor) -> list[TaskPublic]:
    query = Task_T.select("*").get_sql()
    return [TaskPublic.from_row(row) for row in cur.execute(query).fetchall()]


def fetch_all_tasks_by_stage_id(cur: Cursor, stage_id: int) -> list[TaskPublic]:
    query = Task_T.select("*").where(Task_T.stage_id == stage_id).get_sql()
    return [TaskPublic.from_row(row) for row in cur.execute(query).fetchall()]


def fetch_task_by_id(cur: Cursor, id: int) -> TaskPublic | None:
    query = Task_T.select("*").where(Task_T.id == id).get_sql()
    row = cur.execute(query).fetchone()
    if not row:
        return None
    return TaskPublic.from_row(row)


def insert_stage(cur: Cursor, stage: StageCreate) -> StagePublic:
    query = Query.into(Stage_T).columns("name").insert(stage.name).get_sql()
    cur = cur.execute(query)

    last_id = cur.lastrowid
    if not last_id:
        raise RuntimeError(f"error inserting row {stage} into {Stage_T}")
    new_stage = fetch_stage_by_id(cur, last_id)
    assert new_stage is not None
    return new_stage


def update_same_stage_positions(
    cur: Cursor,
    stage_id: int,
    prev_position: int,
    new_position: int,
):
    if prev_position == new_position:
        return

    # moved forward in same stage
    if prev_position > new_position:
        query = (
            Query.update(Task_T)
            .set(Task_T.position, Task_T.position + 1)
            .where(Task_T.stage_id == stage_id)
            .where(new_position <= Task_T.position)
            .where(Task_T.position < prev_position)
            .get_sql()
        )
    else:
        query = (
            Query.update(Task_T)
            .set(Task_T.position, Task_T.position - 1)
            .where(Task_T.stage_id == stage_id)
            .where(
                (prev_position < Task_T.position) & (Task_T.position <= new_position)
            )
            .get_sql()
        )

    cur.execute(query)


def update_old_stage_positions(
    cur: Cursor,
    stage_id: int,
    prev_position: int,
):
    query = (
        Query.update(Task_T)
        .set(Task_T.position, Task_T.position - 1)
        .where(Task_T.stage_id == stage_id)
        .where(Task_T.position > prev_position)
        .get_sql()
    )
    cur.execute(query)


def update_new_stage_positions(
    cur: Cursor,
    stage_id: int,
    position: int,
):
    query = (
        Query.update(Task_T)
        .set(Task_T.position, Task_T.position + 1)
        .where(Task_T.stage_id == stage_id)
        .where(Task_T.position >= position)
        .get_sql()
    )
    cur.execute(query)


def patch_task(cur: Cursor, task_id: int, patched_task: TaskUpdate) -> TaskPublic:
    old_task = fetch_task_by_id(cur, task_id)
    if not old_task:
        raise NotFound(model="Task", id=task_id)

    fields = patched_task.model_dump(exclude_unset=True, exclude={"id"})
    if not fields:
        raise NoFieldsToUpdate

    previous_stage_id = old_task.stage_id
    new_stage_id = patched_task.stage_id if patched_task.stage_id else previous_stage_id

    if previous_stage_id == new_stage_id:
        update_same_stage_positions(
            cur, previous_stage_id, old_task.position, patched_task.position
        )
    else:
        update_old_stage_positions(cur, previous_stage_id, old_task.position)
        update_new_stage_positions(cur, new_stage_id, patched_task.position)

    update_query = Query.update(Task_T).where(Task_T.id == task_id)
    for k, v in fields.items():
        update_query = update_query.set(k, v)

    update_query = update_query.get_sql()
    cur = cur.execute(update_query)

    if cur.rowcount == 0:
        raise NotFound(model="Task", id=task_id)

    if cur.rowcount > 1:
        raise MultipleRowsUpdated(cur.rowcount)

    assert cur.rowcount == 1, "Rowcount must be 1 here"

    updated_task = fetch_task_by_id(cur, task_id)
    assert updated_task is not None

    return updated_task
