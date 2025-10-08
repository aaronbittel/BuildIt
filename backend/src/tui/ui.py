from __future__ import annotations

import curses
import time
from dataclasses import dataclass

from src.tui.event import BoardEvent
from src.tui.layout import Layout, Point
from src.tui.utils import COLOR_BASE_INDEX, FADE_LENGTH


@dataclass
class UIContext:
    stdscr: curses.window
    rows: int
    cols: int

    uistate: UiState
    layout: Layout | None = None
    event_type: BoardEvent | None = None


@dataclass
class UiState:
    active_id: Id | None = None
    key: int = -1
    key_consumed: bool = False

    hover_open: bool = False
    hover_text: str = ""
    cursor_pos: Point | None = None

    textfield_open: bool = False
    textfield_str: str = ""

    status_message: str | None = None
    status_message_pair_number: int = COLOR_BASE_INDEX
    duration: float | None = None
    start_time_ns: int | None = None

    def init_status_message(self, msg: str, duration: float) -> None:
        self.status_message = msg
        self.status_message_pair_number = COLOR_BASE_INDEX
        self.duration = duration
        self.start_time_ns = time.monotonic_ns()

    def status_message_color(self) -> int:
        assert self.start_time_ns is not None
        assert self.duration is not None

        dur = (time.monotonic_ns() - self.start_time_ns) / 10**9
        if dur < self.duration:
            return COLOR_BASE_INDEX

        # TODO: Not to sure about this
        self.status_message_pair_number += 1
        if self.status_message_pair_number >= COLOR_BASE_INDEX + FADE_LENGTH:
            self.status_message = None
            self.status_message_pair_number = COLOR_BASE_INDEX
            self.duration = None
            self.start_time_ns = None

        return self.status_message_pair_number


type Id = int


def widget_id(label: str, instance: int = 0) -> Id:
    import hashlib

    unique_str = f"{label}:{instance}"
    return int(hashlib.sha1(unique_str.encode()).hexdigest(), 16)
