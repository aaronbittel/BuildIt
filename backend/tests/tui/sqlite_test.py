from pathlib import Path
from typing import Callable
from uuid import UUID

import pytest

from src.tui.board import Board, Stage, Task
from src.tui.sqlite import SqliteStorage

DEBUG_DB = Path("debug.db")


@pytest.fixture()
def in_memory_store() -> SqliteStorage:
    return SqliteStorage(":memory:")


@pytest.fixture()
def debug_store() -> SqliteStorage:
    DEBUG_DB.unlink(missing_ok=True)
    return SqliteStorage(DEBUG_DB)


def empty_board() -> Board:
    return Board(title="Empty Board")


def one_level_board() -> Board:
    return Board(
        title="Hello, World",
        selected=1,
        stages=[
            Stage(
                title="My First Stage",
                tasks=[Task(name="Todo 1"), Task(name="Todo 2")],
                selected=0,
            ),
            Stage(title="My Second Stage", tasks=[]),
            Stage(
                title="My Third Stage",
                tasks=[Task(name="Done 1"), Task(name="Done 2"), Task(name="Done 3")],
                selected=2,
            ),
        ],
    )


def simple_nested_board() -> Board:
    return Board(
        title="Nested Board",
        stages=[
            Stage(
                title="Backlog",
                tasks=[
                    Task("Todo 1", next_board=Board(title="Level 2")),
                ],
            ),
        ],
    )


def deeply_nested_board() -> Board:
    return Board(
        title="Main Board",
        stages=[
            Stage(
                "Backlog",
                tasks=[
                    Task(
                        "Todo 1",
                        next_board=Board(
                            title="Level 2",
                            stages=[
                                Stage(
                                    title="My Stage",
                                    tasks=[
                                        Task(name="Task 1.1"),
                                        Task(name="Task 1.2"),
                                    ],
                                )
                            ],
                        ),
                    ),
                    Task("Todo 2"),
                ],
            ),
            Stage(
                "In Progress", tasks=[Task("Task 1"), Task("Task 2"), Task("Task 3")]
            ),
            Stage(
                "Done",
                tasks=[
                    Task("Done 1"),
                    Task("Done 2"),
                    Task("Done 3"),
                ],
            ),
        ],
    )


board_factories = [
    empty_board,
    one_level_board,
    simple_nested_board,
    deeply_nested_board,
]


@pytest.mark.parametrize("make_board", board_factories)
def test_store_board(
    debug_store: SqliteStorage, make_board: Callable[[], Board]
) -> None:
    board = make_board()
    debug_store.save_board(board)
    assert_board_in_db(debug_store, board)


@pytest.mark.parametrize("make_board", board_factories)
def test_store_and_load_board(
    in_memory_store: SqliteStorage, make_board: Board
) -> None:
    board = make_board()
    in_memory_store.save_board(board)

    restored_board = in_memory_store.load_board()
    assert board == restored_board


def assert_board_in_db(store: SqliteStorage, board: Board) -> None:
    # --- Check the board itself ---
    id, title, prev_board_id, selected = store.conn.execute(
        "SELECT id, title, prev_board_id, selected FROM board WHERE id = ?",
        (str(board.id),),
    ).fetchone()

    assert UUID(id) == board.id
    assert title == board.title
    if prev_board_id is None:
        assert prev_board_id == board.prev_board
    else:
        assert UUID(prev_board_id) == board.prev_board.id
    assert selected == board.selected

    # --- Check the stages of the board ---
    for i, stage in enumerate(board.stages):
        stage_title, stage_selected = store.conn.execute(
            "SELECT title, selected FROM stage WHERE id = ?", (str(stage.id),)
        ).fetchone()
        assert stage_title == stage.title
        assert stage_selected == stage.selected

        stage_position = store.conn.execute(
            "SELECT position FROM board_stage_link WHERE board_id = ? AND stage_id = ?",
            (str(board.id), str(stage.id)),
        ).fetchone()[0]
        assert stage_position == i

        # --- Check tasks within this stage ---
        for j, task in enumerate(stage.tasks):
            task_name, task_next_board_id = store.conn.execute(
                "SELECT name, next_board_id FROM task WHERE id = ?", (str(task.id),)
            ).fetchone()
            assert task_name == task.name
            if task_next_board_id is None:
                assert task_next_board_id == task.next_board
            else:
                assert task.next_board is not None
                assert UUID(task_next_board_id) == task.next_board.id

            task_position = store.conn.execute(
                "SELECT position FROM stage_task_link WHERE stage_id = ? AND task_id = ?",
                (str(stage.id), str(task.id)),
            ).fetchone()[0]
            assert task_position == j

            # --- Recursively check if the task has a next board ---
            if task.next_board is not None:
                assert_board_in_db(store, task.next_board)
