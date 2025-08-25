import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.dev_utils import DB_SNAPSHOTS_PATH, router
from src.helpers import (
    CursorDep,
    init_schema,
    init_conn,
    load_schema_into_db,
)
from src.repository import (
    MultipleRowsUpdated,
    NoFieldsToUpdate,
    delete_task_by_id,
    fetch_all_tasks,
    fetch_stages_with_tasks,
    fetch_task_by_id,
    insert_stage,
    insert_task,
    patch_task,
    DEFAULT_SCHEMA,
    update_task_ordering,
)
from src.schemas import (
    StageCreate,
    StageDetail,
    TaskCreate,
    TaskMoveUpdate,
    TaskNameUpdate,
    TaskPublic,
)

logging.basicConfig()

load_dotenv()
_db_path = os.getenv("SQLITE_DATABASE_PATH")
assert _db_path is not None
DB_PATH = Path(_db_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = init_conn(DB_PATH)
    cur = conn.cursor()
    cur = init_schema(cur, DEFAULT_SCHEMA)

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

app.include_router(router)


@app.get("/")
def hello_world():
    return {"hello": "world"}


@app.get("/tasks", response_model=list[StageDetail])
def get_all_tasks(cur: CursorDep):
    return fetch_all_tasks(cur)


@app.post("/tasks", status_code=HTTP_201_CREATED, response_model=TaskPublic)
def create_task(cur: CursorDep, newTask: TaskCreate):
    new_task = insert_task(cur, newTask)
    cur.connection.commit()
    return new_task


# FIXME: do this better
def update_task_or_fail(
    cur: CursorDep,
    task_id: int,
    task: TaskMoveUpdate | TaskNameUpdate,
) -> TaskPublic:
    """Patch a task and commit, handling exceptions."""
    try:
        updated_task = patch_task(cur, task_id, task)
    except NoFieldsToUpdate as e:
        raise HTTPException(HTTP_400_BAD_REQUEST, detail=str(e))
    except MultipleRowsUpdated as e:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return updated_task


@app.patch("/tasks/{task_id}/move", response_model=list[StageDetail])
def update_task_move(cur: CursorDep, task_id: int, moved_task: TaskMoveUpdate):
    old_task = fetch_task_by_id(cur, task_id)
    if not old_task:
        raise HTTPException(
            HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not Found"
        )

    update_task_ordering(cur, old_task, moved_task)
    update_task_or_fail(cur, task_id, moved_task)
    cur.connection.commit()

    return fetch_stages_with_tasks(cur, sorted=True)


@app.patch("/tasks/{task_id}", response_model=TaskPublic)
def update_task(cur: CursorDep, task_id: int, renamed_task: TaskNameUpdate):
    return update_task_or_fail(cur, task_id, renamed_task)


@app.get("/stages/tasks", response_model=list[StageDetail])
def get_stages_with_tasks(cur: CursorDep):
    return fetch_stages_with_tasks(cur, sorted=True)


@app.post("/reset")
def reset_db(request: Request):
    current = DB_SNAPSHOTS_PATH / "current.sql"
    snapshot = current.read_text() if current.exists() else DEFAULT_SCHEMA

    load_schema_into_db(request, DB_PATH, snapshot)
    return {"message": f"Successfully reset db {DB_PATH}"}


@app.delete("/tasks/{task_id}", status_code=HTTP_204_NO_CONTENT)
def delete_task(cur: CursorDep, task_id: int):
    rowcount = delete_task_by_id(cur, task_id)
    if rowcount == 0:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Task not found")

    assert rowcount == 1, "Noway4u_sir"


@app.post("/stages", status_code=HTTP_201_CREATED)
def create_stage(cur: CursorDep, stage: StageCreate):
    try:
        created_stage = insert_stage(cur, stage)
    except sqlite3.IntegrityError:
        logging.exception("stage name must be unique")
        raise HTTPException(HTTP_409_CONFLICT, detail="Stage name must be unique")
    cur.connection.commit()
    return StageDetail(**created_stage.model_dump(), tasks=[])
