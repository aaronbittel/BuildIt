import logging
import sqlite3
from pathlib import Path
from sqlite3 import Connection
from uuid import UUID

from src.tui.board import Board, Stage, Task
from src.tui.storage import Storage

type UUIDStr = str

CREATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS board (
    id TEXT PRIMARY KEY,
    title VARCHAR NOT NULL,
    prev_board_id INTEGER NULL DEFAULT NULL REFERENCES board(id),
    selected INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS stage (
    id TEXT PRIMARY KEY,
    title VARCHAR NOT NULL,
    selected INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS task (
    id TEXT PRIMARY KEY,
    name VARCHAR NOT NULL,
    next_board_id TEXT NULL DEFAULT NULL REFERENCES board(id)
);

CREATE TABLE IF NOT EXISTS board_stage_link (
    board_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (board_id, stage_id),
    FOREIGN KEY (board_id) REFERENCES board(id),
    FOREIGN KEY (stage_id) REFERENCES stage(id)
);

CREATE TABLE IF NOT EXISTS stage_task_link (
    stage_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (stage_id, task_id),
    FOREIGN KEY (stage_id) REFERENCES stage(id),
    FOREIGN KEY (task_id) REFERENCES task(id)
);
"""


class SqliteStorage(Storage):
    def __init__(self, path: Path) -> None:
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
        self.conn = sqlite3.connect(self.path)
        self.conn.executescript(CREATE_SCHEMA)
        self.conn.commit()

    def get_state(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM app_state WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    def set_state(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO app_state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    def get_board_root_id(self) -> UUID:
        cur = self.conn.execute("SELECT id FROM board WHERE prev_board_id IS NULL")
        return UUID(cur.fetchone()[0])

    def get_leaf_task_id(self) -> UUID:
        cur = self.conn.execute("SELECT id FROM task WHERE next_board_id IS NULL")
        return cur.fetchone()[0]

    def save_board(self, board: Board) -> None:
        self.path.unlink()
        self._init_db()
        logging.info("SAVING")
        self.set_state("selected_board_id", str(board.id))
        root = board.root_board()
        self._add_board(root)

    def load_board(self) -> Board:
        logging.info("LOADING BOARD")
        board = self._load_board(board_id=self.get_board_root_id())
        selected_board_id = UUID(self.get_state("selected_board_id"))
        return board.find_board(selected_board_id)

    def _load_board(
        self, board_id: UUID, parent_board_idstr: UUIDStr | None = None
    ) -> Board:
        with self.conn as conn:
            title, selected = conn.execute(
                "SELECT title, selected FROM board WHERE id = ?", (str(board_id),)
            ).fetchone()
            return Board(
                id=board_id,
                title=title,
                prev_board=None,  # this will be corrected in __post_init__
                selected=selected,
                stages=self._load_stages(conn, str(board_id)),
            )

    def _load_stages(self, conn: Connection, board_id: str) -> list[Stage]:
        cur = conn.execute(
            "SELECT stage_id, position FROM board_stage_link WHERE board_id = ?",
            (board_id,),
        )
        stages: list[Stage] = []
        for stage_id, _ in sorted(cur.fetchall(), key=lambda row: row[1]):
            cur = conn.execute(
                "SELECT title, selected FROM stage WHERE id = ?", (stage_id,)
            )
            title, selected = cur.fetchone()
            stages.append(
                Stage(
                    id=UUID(stage_id),
                    title=title,
                    selected=selected,
                    tasks=self._load_tasks(conn, stage_id, parent_board_id=board_id),
                )
            )
        return stages

    def _load_tasks(
        self, conn: Connection, stage_id: int, parent_board_id: str
    ) -> list[Task]:
        cur = conn.execute(
            "SELECT task_id, position FROM stage_task_link WHERE stage_id = ?",
            (stage_id,),
        )
        tasks: list[Task] = []
        for task_id, _ in sorted(cur.fetchall(), key=lambda row: row[1]):
            cur = conn.execute(
                "SELECT name, next_board_id FROM task WHERE id = ?", (task_id,)
            )
            name, next_board_id = cur.fetchone()
            tasks.append(
                Task(
                    id=UUID(task_id),
                    name=name,
                    next_board=self._load_board(
                        UUID(next_board_id), parent_board_idstr=parent_board_id
                    )
                    if next_board_id is not None
                    else None,
                )
            )
        return tasks

    def _add_board(self, board: Board) -> None:
        with self.conn as conn:
            conn.execute(
                "INSERT INTO board (id, title, prev_board_id, selected) "
                "VALUES (?, ?, ?, ?)",
                (
                    str(board.id),
                    board.title,
                    str(board.prev_board.id) if board.prev_board is not None else None,
                    board.selected,
                ),
            )
            stages = [
                (str(stage.id), stage.title, stage.selected) for stage in board.stages
            ]
            conn.executemany(
                "INSERT INTO stage (id, title, selected) VALUES (?, ?, ?)", stages
            )

            tasks = [
                (
                    str(task.id),
                    task.name,
                    str(task.next_board.id) if task.next_board is not None else None,
                )
                for stage in board.stages
                for task in stage.tasks
            ]
            conn.executemany(
                "INSERT INTO task (id, name, next_board_id) VALUES (?, ?, ?)", tasks
            )

            board_stage_links = [
                (str(board.id), str(stage.id), i)
                for i, stage in enumerate(board.stages)
            ]
            conn.executemany(
                "INSERT INTO board_stage_link (board_id, stage_id, position) "
                "VALUES (?, ?, ?)",
                board_stage_links,
            )

            stage_task_links = [
                (str(stage.id), str(task.id), i)
                for stage in board.stages
                for i, task in enumerate(stage.tasks)
            ]
            conn.executemany(
                "INSERT INTO stage_task_link (stage_id, task_id, position) "
                "VALUES (?, ?, ?)",
                stage_task_links,
            )

            for stage in board.stages:
                for task in stage.tasks:
                    if task.next_board is not None:
                        self._add_board(task.next_board)


if __name__ == "__main__":
    path = Path("./version_0_1.db")
    path.unlink(missing_ok=True)
    store = SqliteStorage(path)

    board = Board(
        title="Version 0.1",
        # stages=[
        #     Stage(title="Backlog", tasks=[Task(name="Todo 1"), Task(name="Todo 2")])
        # ],
    )
    store.save_board(board)
