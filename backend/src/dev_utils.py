from __future__ import annotations

import datetime as dt
import logging
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel as BaseSchema
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.helpers import load_schema_into_db

logging.basicConfig(level=logging.INFO)


load_dotenv()
_db_path_ = os.getenv("SQLITE_DATABASE_PATH")
assert _db_path_ is not None
DB_PATH = Path(_db_path_)

DB_SNAPSHOTS_PATH = Path("./db_snapshots")
DB_SNAPSHOTS_PATH.mkdir(exist_ok=True)

SQL_COMMENT = "--"
DATE_FORMAT_FOR_FILENAME = "%Y-%m-%d_%H-%M-%S"
DATE_FORMAT_TEXT = "%Y-%m-%d %H:%M:%S"


router = APIRouter(prefix="/dev")


class SnapshotCreate(BaseSchema):
    name: str | None = None
    comment: str


@router.post("/dbstate/save", status_code=HTTP_201_CREATED)
def save_dummy(req: SnapshotCreate):
    now = dt.datetime.now()
    filename = req.name if req.name else now.strftime(DATE_FORMAT_FOR_FILENAME)
    snapshot_path = DB_SNAPSHOTS_PATH / f"{filename}.sql"
    try:
        result = subprocess.run(
            ["sqlite3", str(DB_PATH), ".dump"],
            capture_output=True,
            text=True,
            check=True,
        )
        text = (
            f"{SQL_COMMENT} COMMENT: {req.comment}\n"
            f"{SQL_COMMENT} DATE: {now.strftime(DATE_FORMAT_TEXT)}\n"
            f"{result.stdout}"
        )
        snapshot_path.write_text(text)
    except subprocess.CalledProcessError as e:
        logging.exception(
            "Dumping sqlite db %s failed\nReturn Code: %d\nStdout: %s\nStderr: %s",
            DB_PATH,
            e.returncode,
            e.stdout,
            e.stderr,
        )
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR, detail="dumping db file failed"
        )


@router.get("/dbstate", response_model=list[str])
def get_dbstate_comments():
    comments: list[str] = []
    for file in DB_SNAPSHOTS_PATH.glob("*.sql"):
        with file.open() as f:
            comment = f.readline()
            assert comment.startswith(SQL_COMMENT)
            comment = comment[len(SQL_COMMENT) :].strip()
            comments.append(comment)
    return comments


@router.post("/dbstate/load")
def load_dbstate(
    request: Request,
    date: str | None = None,
    name: str | None = None,
):
    if date is None and name is None:
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            detail="either provide a name or a date via query parameters",
        )

    filename = name if name else date
    assert filename is not None

    snapshot_path = DB_SNAPSHOTS_PATH / f"{filename}.sql"
    if not snapshot_path.exists():
        raise HTTPException(
            HTTP_404_NOT_FOUND, detail=f"No snapshot file with {snapshot_path} found"
        )

    schema = snapshot_path.read_text(encoding="utf-8")
    load_schema_into_db(request, DB_PATH, schema)
    return {"message": f"Successfully load snapshot {filename}"}
