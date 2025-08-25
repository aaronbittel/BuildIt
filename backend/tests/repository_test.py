from pathlib import Path
from sqlite3 import Cursor
from typing import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK

from src.main import app, init_schema, init_conn
from src.repository import (
    fetch_all_tasks_by_stage_id,
    fetch_task_by_id,
    insert_stage,
    insert_task,
    DEFAULT_SCHEMA,
)
from src.schemas import StageCreate, StagePublic, TaskCreate, TaskPublic


@pytest.fixture(name="client")
def client_fixture(cur: Cursor) -> Generator[TestClient, None, None]:
    app.state.conn = cur.connection
    app.state.cur = cur

    yield TestClient(app)


@pytest.fixture(name="cur")
def cursor_fixture() -> Generator[Cursor, None, None]:
    conn = init_conn(Path(":memory:"))
    cur = conn.cursor()
    cur = init_schema(cur, DEFAULT_SCHEMA)

    yield cur

    cur.close()
    conn.close()


@pytest.fixture(name="setup_stage_tasks")
def setup_stage_tasks_fixture(
    cur: Cursor,
) -> Callable[..., tuple[StagePublic, list[TaskPublic]]]:
    def _create(stage_name: str, *task_names: str):
        stage = insert_stage(cur, StageCreate(name=stage_name))
        return stage, [
            insert_task(cur, TaskCreate(name=name, stage_id=stage.id))
            for name in task_names
        ]

    return _create


@pytest.fixture(name="setup_stage_with_n_tasks")
def setup_stage_with_n_tasks_fixture(
    cur: Cursor,
) -> Callable[..., tuple[StagePublic, list[TaskPublic]]]:
    def _create(stage_name: str, num_tasks: int):
        stage = insert_stage(cur, StageCreate(name=stage_name))
        tasks = [
            insert_task(cur, TaskCreate(name=f"Task {i + 1}", stage_id=stage.id))
            for i in range(num_tasks)
        ]
        return stage, tasks

    return _create


def test_reorder_task_within_stage(
    client: TestClient,
    cur: Cursor,
    setup_stage_with_n_tasks: Callable[..., tuple[StagePublic, list[TaskPublic]]],
) -> None:
    stage, tasks = setup_stage_with_n_tasks("Test Stage", 5)
    dragged_task = tasks[3]
    target_position = 1

    response = client.patch(
        f"/tasks/{dragged_task.id}/move",
        json={"stage_id": stage.id, "to_index": target_position},
    )
    assert response.status_code == HTTP_200_OK

    updated_task = fetch_task_by_id(cur, dragged_task.id)
    assert updated_task is not None

    assert updated_task.id == dragged_task.id
    assert updated_task.stage_id == dragged_task.stage_id
    assert updated_task.position == target_position

    updated_tasks = fetch_all_tasks_by_stage_id(cur, stage.id)

    assert set(map(lambda task: task.position, updated_tasks)) == set(range(0, 5))


def test_reorder_task_new_stage(
    client: TestClient,
    cur: Cursor,
    setup_stage_with_n_tasks: Callable[..., tuple[StagePublic, list[TaskPublic]]],
) -> None:
    old_stage_length = 5
    new_stage_length = 5
    old_stage, old_stage_tasks = setup_stage_with_n_tasks("Old Stage", old_stage_length)
    new_stage, _ = setup_stage_with_n_tasks("New Stage", new_stage_length)

    dragged_task = old_stage_tasks[3]
    target_position_new_stage = 3

    response = client.patch(
        f"/tasks/{dragged_task.id}/move",
        json={
            "stage_id": new_stage.id,
            "to_index": target_position_new_stage,
        },
    )
    assert response.status_code == HTTP_200_OK

    updated_task = fetch_task_by_id(cur, dragged_task.id)
    assert updated_task is not None

    assert updated_task.id == dragged_task.id
    assert updated_task.stage_id == new_stage.id
    assert updated_task.position == target_position_new_stage

    updated_old_tasks = fetch_all_tasks_by_stage_id(cur, old_stage.id)
    assert set(map(lambda task: task.position, updated_old_tasks)) == set(
        range(0, old_stage_length - 1)
    )

    updated_new_tasks = fetch_all_tasks_by_stage_id(cur, new_stage.id)
    assert set(map(lambda task: task.position, updated_new_tasks)) == set(
        range(0, new_stage_length + 1)
    )
