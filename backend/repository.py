from __future__ import annotations

from sqlite3 import Cursor

from pypika import Query, Table

from schemas import (
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
    FOREIGN KEY (stage_id) REFERENCES stage(id)
);

INSERT INTO stage (name) VALUES ('Backlog'), ('In Progress'), ('Done');

INSERT INTO task (name, stage_id)
VALUES
('add more metadata to the tasks', 1),
('Order of item depends on drag position', 1),
('create a backend', 3);
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
    stages_query = Stage_T.select("*").get_sql()

    stages = [StageDetail.from_row(row) for row in cur.execute(stages_query).fetchall()]
    for stage in stages:
        task_query = Task_T.select("*").where(Task_T.stage_id == stage.id).get_sql()
        stage.tasks.extend(
            [TaskPublic.from_row(row) for row in cur.execute(task_query).fetchall()]
        )

    return stages


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


def insert_task(cur: Cursor, task: TaskCreate) -> TaskPublic:
    query = (
        Query.into(Task_T)
        .columns("name", "stage_id")
        .insert(task.name, task.stage_id)
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


def fetch_task_by_id(cur: Cursor, id: int) -> TaskPublic | None:
    query = Task_T.select("*").where(Task_T.id == id).get_sql()
    row = cur.execute(query).fetchone()
    if not row:
        return None
    return TaskPublic.from_row(row)


def insert_stage(cur: Cursor, stage: StageCreate) -> int:
    query = Query.into(Stage_T).columns("name").insert(stage.name).get_sql()
    cur = cur.execute(query)

    last_id = cur.lastrowid
    if not last_id:
        raise RuntimeError(f"error inserting row {stage} into {Stage_T}")
    return last_id


def patch_task(cur: Cursor, task_id, patched_task: TaskUpdate) -> TaskPublic:
    query = Query.update(Task_T).where(Task_T.id == task_id)
    fields = patched_task.model_dump(exclude_unset=True, exclude=set("id"))
    if not fields:
        raise NoFieldsToUpdate

    for k, v in fields.items():
        query = query.set(k, v)

    query = query.get_sql()
    cur = cur.execute(query)

    if cur.rowcount == 0:
        raise NotFound(model="Task", id=task_id)

    if cur.rowcount > 1:
        raise MultipleRowsUpdated(cur.rowcount)

    assert cur.rowcount == 1, "Rowcount must be 1 here"

    updated_task = fetch_task_by_id(cur, task_id)
    assert updated_task is not None

    return updated_task
