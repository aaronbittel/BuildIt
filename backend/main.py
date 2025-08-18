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

from repository import (
    MultipleRowsUpdated,
    NoFieldsToUpdate,
    NotFound,
    fetch_all_tasks,
    fetch_stages_with_tasks,
    insert_task,
    patch_task,
    schema,
)
from schemas import TaskCreate, TaskPublic, TaskUpdate

logging.basicConfig()

DB_PATH = Path("./buildit.db")


def init_conn() -> Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: Connection) -> Cursor:
    """Initialize the database schema and return a cursor."""
    cur = conn.cursor()
    cur.executescript(schema)
    conn.commit()
    return cur


@asynccontextmanager
async def lifespan(app: FastAPI):
    DB_PATH.unlink(missing_ok=True)

    conn = init_conn()
    cur = init_db(conn)

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


@app.patch("/tasks/{task_id}", response_model=TaskPublic)
def update_task(cur: CursorDep, task_id: int, patched_task: TaskUpdate):
    try:
        updated_task = patch_task(cur, task_id, patched_task)
        cur.connection.commit()
    except NoFieldsToUpdate as e:
        raise HTTPException(HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFound as e:
        raise HTTPException(HTTP_404_NOT_FOUND, detail=str(e))
    except MultipleRowsUpdated as e:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return updated_task


@app.get("/stages/tasks")
def get_stages_with_tasks(cur: CursorDep):
    return fetch_stages_with_tasks(cur)


@app.post("/reset")
def reset_db():
    app.state.cur.close()
    app.state.conn.close()

    DB_PATH.unlink(missing_ok=True)

    conn = init_conn()
    cur = init_db(conn)

    app.state.conn = conn
    app.state.cur = cur

    return get_stages_with_tasks(cur)
