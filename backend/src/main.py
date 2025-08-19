import logging
import sqlite3
from collections.abc import Generator
from contextlib import asynccontextmanager
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.repository import (
    MultipleRowsUpdated,
    NoFieldsToUpdate,
    NotFound,
    fetch_all_tasks,
    fetch_stages_with_tasks,
    insert_stage,
    insert_task,
    patch_task,
    schema,
)
from src.schemas import StageCreate, StageDetail, TaskCreate, TaskPublic, TaskUpdate

logging.basicConfig()

DB_PATH = "./buildit.db"


def init_conn(path: str) -> Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(cur: Cursor) -> Cursor:
    """Initialize the database schema and return a cursor."""
    cur.executescript(schema)
    cur.connection.commit()
    return cur


def initial_data(cur: Cursor) -> None:
    backlog = insert_stage(cur, StageCreate(name="Backlog"))
    in_progess = insert_stage(cur, StageCreate(name="In Progress"))
    done = insert_stage(cur, StageCreate(name="Done"))

    insert_task(
        cur,
        TaskCreate(
            name="add feat to update task name",
            stage_id=backlog.id,
        ),
    )

    insert_task(
        cur,
        TaskCreate(
            name="add feat to update stage name",
            stage_id=backlog.id,
        ),
    )

    insert_task(
        cur,
        TaskCreate(
            name="add creating more stages",
            stage_id=backlog.id,
        ),
    )

    insert_task(
        cur,
        TaskCreate(
            name="add removing / hidding stages",
            stage_id=backlog.id,
        ),
    )

    insert_task(
        cur,
        TaskCreate(
            name="add more metadata to the tasks",
            stage_id=backlog.id,
        ),
    )

    cur.connection.commit()


def tables_exists(cur: Cursor) -> bool:
    try:
        cur.execute("SELECT 1 FROM task").fetchone()
    except sqlite3.OperationalError:
        return False
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = init_conn(DB_PATH)
    cur = conn.cursor()
    if not tables_exists(cur):
        cur = create_tables(cur)
        initial_data(cur)

    app.state.conn = conn
    app.state.cur = cur

    yield

    cur.close()
    conn.close()


app = FastAPI(title="BuildIt! Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_cursor() -> Generator[Cursor]:
    try:
        yield app.state.cur
    except Exception:
        app.state.cur.connection.rollback()
        raise


CursorDep = Annotated[Cursor, Depends(get_cursor)]


@app.get("/")
def hello_world():
    return {"hello": "world"}


@app.get("/tasks", response_model=list[TaskPublic])
def get_all_tasks(cur: CursorDep):
    return fetch_all_tasks(cur)


@app.post("/tasks", status_code=HTTP_201_CREATED, response_model=TaskPublic)
def create_task(cur: CursorDep, newTask: TaskCreate):
    new_task = insert_task(cur, newTask)
    cur.connection.commit()
    return new_task


@app.patch("/tasks/{task_id}", response_model=list[StageDetail])
def update_task(cur: CursorDep, task_id: int, patched_task: TaskUpdate):
    try:
        patch_task(cur, task_id, patched_task)
        cur.connection.commit()
    except NoFieldsToUpdate as e:
        raise HTTPException(HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFound as e:
        raise HTTPException(HTTP_404_NOT_FOUND, detail=str(e))
    except MultipleRowsUpdated as e:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    stages = fetch_stages_with_tasks(cur)
    for stage in stages:
        stage.tasks.sort(key=lambda t: t.position)
    return stages


@app.get("/stages/tasks", response_model=list[StageDetail])
def get_stages_with_tasks(cur: CursorDep):
    stages = fetch_stages_with_tasks(cur)
    for stage in stages:
        stage.tasks.sort(key=lambda t: t.position)
    return stages


@app.post("/reset")
def reset_db():
    app.state.cur.close()
    app.state.conn.close()

    Path(DB_PATH).unlink(missing_ok=True)

    conn = init_conn(DB_PATH)
    cur = conn.cursor()
    cur = create_tables(cur)
    initial_data(cur)

    app.state.conn = conn
    app.state.cur = cur

    return get_stages_with_tasks(cur)
