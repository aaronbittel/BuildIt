from typing import Protocol

from src.tui.board import Board


class Storage(Protocol):
    def load_board(self) -> Board: ...

    def save_board(self, board: Board) -> None: ...


class DummyStorage(Storage):
    def load_board(self) -> Board:
        return Board.default(title="Default Storage Board", prefilled=True)

    def save_board(self, board: Board) -> None:
        pass
