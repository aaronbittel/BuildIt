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
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.helpers import load_schema_into_db
from src.repository import DEFAULT_SCHEMA

logging.basicConfig(level=logging.INFO)


load_dotenv()
_db_path_ = os.getenv("SQLITE_DATABASE_PATH")
assert _db_path_ is not None
DB_PATH = Path(_db_path_)

DB_SNAPSHOTS_PATH = Path("./db_snapshots")
DB_SNAPSHOTS_PATH.mkdir(exist_ok=True)
CURRENT_SNAPSHOT_PATH = DB_SNAPSHOTS_PATH / ".current"
DEFAULT_SNAPSHOT_PATH = DB_SNAPSHOTS_PATH / "default.sql"

SQL_COMMENT = "--"
SNAPSHOT_COMMENT = f"{SQL_COMMENT} COMMENT: "
SNAPSHOT_DATE = f"{SQL_COMMENT} DATE: "
DATE_FORMAT_TEXT = "%Y-%m-%d %H:%M:%S"


def write_schema_to_file(
    path: Path,
    comment: str,
    date: dt.datetime,
    schema: str,
) -> None:
    text = (
        f"{SNAPSHOT_COMMENT}{comment}\n"
        f"{SNAPSHOT_DATE}{date.strftime(DATE_FORMAT_TEXT)}\n"
        f"{schema}"
    )
    path.write_text(text)


if not DEFAULT_SNAPSHOT_PATH.exists():
    write_schema_to_file(
        DEFAULT_SNAPSHOT_PATH,
        "Empty schema with only the table definitions",
        date=dt.datetime.now(),
        schema=DEFAULT_SCHEMA,
    )


router = APIRouter(prefix="/dev")


class SnapshotLoad(BaseSchema):
    name: str


class SnapshotCreate(SnapshotLoad):
    comment: str


class SnapshotPublic(SnapshotCreate):
    date: dt.datetime


# FIXME: add error handling
def parse_snapshot(path: Path) -> SnapshotPublic:
    name = path.name
    with path.open() as f:
        comment = f.readline().strip().removeprefix(SNAPSHOT_COMMENT)
        date_str = f.readline().strip().removeprefix(SNAPSHOT_DATE)
        date = dt.datetime.strptime(date_str, DATE_FORMAT_TEXT)
    return SnapshotPublic(name=name, comment=comment, date=date)


@router.post(
    "/snapshots/save",
    status_code=HTTP_201_CREATED,
    response_model=SnapshotPublic,
)
def save_dummy(snapshot: SnapshotCreate):
    now = dt.datetime.now()
    snapshot_path = DB_SNAPSHOTS_PATH / f"{snapshot.name}.sql"
    try:
        result = subprocess.run(
            ["sqlite3", str(DB_PATH), ".dump"],
            capture_output=True,
            text=True,
            check=True,
        )
        write_schema_to_file(
            snapshot_path, snapshot.comment, date=now, schema=result.stdout
        )
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
    return SnapshotPublic(
        name=snapshot.name + ".sql", comment=snapshot.comment, date=now
    )


@router.get("/snapshots/current", response_model=SnapshotPublic)
def get_current_snapshot_name():
    if not CURRENT_SNAPSHOT_PATH.exists():
        raise HTTPException(HTTP_404_NOT_FOUND, detail="No current snapshot found")
    current = CURRENT_SNAPSHOT_PATH.read_text().strip()
    return parse_snapshot(Path(current))


@router.get("/snapshots", response_model=list[SnapshotPublic])
def get_all_snapshots():
    return [parse_snapshot(path) for path in DB_SNAPSHOTS_PATH.glob("*.sql")]


@router.post("/snapshots/load")
def load_snapshot(request: Request, snapshot: SnapshotLoad):
    snapshot_path = DB_SNAPSHOTS_PATH / snapshot.name
    if not snapshot_path.exists():
        raise HTTPException(
            HTTP_404_NOT_FOUND, detail=f"No snapshot file with {snapshot_path} found"
        )

    schema = snapshot_path.read_text(encoding="utf-8")
    load_schema_into_db(request, DB_PATH, schema)

    CURRENT_SNAPSHOT_PATH.write_text(str(snapshot_path), encoding="utf-8")
    logging.info("loading snapshot %s", snapshot_path)

    return {"message": f"Successfully load snapshot {snapshot.name}"}
