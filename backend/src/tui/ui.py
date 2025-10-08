from __future__ import annotations

import curses
from dataclasses import dataclass
from typing import Literal

from src.tui.layout import Layout
from src.tui.utils import Point

type Id = int


def widget_id(label: str, instance: int = 0) -> Id:
    import hashlib

    unique_str = f"{label}:{instance}"
    return int(hashlib.sha1(unique_str.encode()).hexdigest(), 16)


@dataclass
class UiState:
    active_id: Id | None = None
    key: int = -1
    key_consumed: bool = False

    hover_open: bool = False
    hover_text: str = ""
    cursor_position: Point | None = None

    textfield_open: bool = False
    textfield_str: str = ""


type BoardEvent = Literal[
    "Add Task",
    "Edit Task",
    "Add Stage",
    "Edit Stage",
    "Saving",
]
type TextfieldEvent = Literal["Continue", "Cancelled", "Accepted"]

type EventType = BoardEvent | TextfieldEvent
type Event = EventType | tuple[BoardEvent, dict[str, str]]


@dataclass
class UIContext:
    stdscr: curses.window
    rows: int
    cols: int

    uistate: UiState
    layout: Layout | None = None
    event_type: BoardEvent | None = None
