from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.tui.board import Board
from src.tui.layout import Point

type BoardEvent = AddTask | EditTask | AddStage | EditStage
type TextfieldEvent = Accepted | Cancelled


@dataclass(frozen=True)
class Event(ABC):
    @abstractmethod
    def __str__(self) -> str: ...


@dataclass(frozen=True)
class AddTask(Event):
    def __str__(self) -> str:
        return "AddTask"


@dataclass(frozen=True)
class EditTask(Event):
    prefill: str

    def __str__(self) -> str:
        return "EditTask"


@dataclass(frozen=True)
class AddStage(Event):
    def __str__(self) -> str:
        return "AddStage"


@dataclass(frozen=True)
class EditStage(Event):
    prefill: str

    def __str__(self) -> str:
        return "EditStage"


@dataclass(frozen=True)
class Accepted(Event):
    def __str__(self) -> str:
        return "Accepted"


@dataclass(frozen=True)
class Cancelled(Event):
    def __str__(self) -> str:
        return "Cancelled"


@dataclass(frozen=True)
class UpdateBoard(Event):
    new_board: Board

    def __str__(self) -> str:
        return "UpdateBoard"


@dataclass(frozen=True)
class ShowHover(Event):
    position: Point
    text: str

    def __str__(self) -> str:
        return "ShowHover"


@dataclass(frozen=True)
class HideHover(Event):
    def __str__(self) -> str:
        return "HideHover"


@dataclass(frozen=True)
class Quit(Event):
    def __str__(self) -> str:
        return "Quit"


@dataclass(frozen=True)
class ShowStatusMessage(Event):
    text: str
    duration: float

    def __str__(self) -> str:
        return "ShowStatusMessage"
