import sqlite3
from collections.abc import Generator
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import Annotated

from fastapi import Depends, Request


def get_cursor(request: Request) -> Generator[Cursor]:
    cur = request.app.state.cur
    try:
        yield cur
    except Exception:
        cur.connection.rollback()
        raise


CursorDep = Annotated[Cursor, Depends(get_cursor)]


def load_schema_into_db(request: Request, db_path: Path, schema: str) -> None:
    request.app.state.cur.close()
    request.app.state.conn.close()

    db_path.unlink(missing_ok=True)

    conn = init_conn(db_path)
    cur = conn.cursor()
    cur = init_schema(cur, schema)

    request.app.state.conn = conn
    request.app.state.cur = cur


def init_conn(path: Path) -> Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(cur: Cursor, schema: str) -> Cursor:
    """Initialize the database schema and return a cursor."""
    cur.executescript(schema)
    cur.connection.commit()
    return cur
