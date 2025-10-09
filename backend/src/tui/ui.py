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
    board_event: BoardEvent | None = None


class StatusMessage:
    def __init__(self, msg: str, color_pair_number: int, duration: float) -> None:
        self.msg = msg
        self.cur_color_pair = color_pair_number
        self.duration = duration
        self.start_time_ns = time.monotonic_ns()

    def next_color(self) -> int | None:
        dur = (time.monotonic_ns() - self.start_time_ns) / 10**9
        if dur < self.duration:
            return COLOR_BASE_INDEX

        # TODO: Not to sure about this
        self.cur_color_pair += 1
        if self.cur_color_pair >= COLOR_BASE_INDEX + FADE_LENGTH:
            return None

        return self.cur_color_pair


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

    status_message: StatusMessage | None = None

    def init_status_message(self, msg: str, duration: float) -> None:
        self.status_message = StatusMessage(
            msg=msg, color_pair_number=COLOR_BASE_INDEX, duration=duration
        )

    def status_message_color(self) -> int | None:
        assert self.status_message is not None
        color = self.status_message.next_color()
        if color is None:
            self.status_message = None
        return color


type Id = int


def widget_id(label: str, instance: int = 0) -> Id:
    import hashlib

    unique_str = f"{label}:{instance}"
    return int(hashlib.sha1(unique_str.encode()).hexdigest(), 16)
