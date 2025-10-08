from __future__ import annotations

from dataclasses import dataclass

from src.tui.board import Board
from src.tui.layout import Point

type BoardEvent = AddTask | EditTask | AddStage | EditStage
type TextfieldEvent = Accepted | Cancelled | Continue
type AppEvent = BoardEvent | TextfieldEvent | UpdateBoard | ShowHover | HideHover | Quit


@dataclass(frozen=True)
class AddTask:
    def __str__(self) -> str:
        return "Add Task"


@dataclass(frozen=True)
class EditTask:
    prefill: str

    def __str__(self) -> str:
        return "Edit Task"


@dataclass(frozen=True)
class AddStage:
    def __str__(self) -> str:
        return "Add Stage"


@dataclass(frozen=True)
class EditStage:
    prefill: str

    def __str__(self) -> str:
        return "Edit Stage"


@dataclass(frozen=True)
class Accepted: ...


@dataclass(frozen=True)
class Cancelled: ...


@dataclass(frozen=True)
class Continue: ...


@dataclass(frozen=True)
class UpdateBoard:
    new_board: Board


@dataclass(frozen=True)
class ShowHover:
    position: Point
    text: str


@dataclass(frozen=True)
class HideHover: ...


@dataclass(frozen=True)
class Quit: ...


@dataclass(frozen=True)
class ShowStatusMessage:
    text: str
