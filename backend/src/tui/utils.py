import curses
from contextlib import contextmanager
from functools import wraps
import logging
from typing import NamedTuple, Self

from src.tui.layout import Rect

ROUNDED_TOPLEFT = "╭"
ROUNDED_TOPRIGHT = "╮"
ROUNDED_BOTTOMRIGHT = "╯"
ROUNDED_BOTTOMLEFT = "╰"
VERTICAL_BAR = "│"
HORIZONTAL_BAR = "─"
ELLIPSIS = "…"

KEY_EXIT = 7
KEY_ENTER = 10
KEY_ESC = 27
KEY_IGNORE = 0


class RGB(NamedTuple):
    r: int
    g: int
    b: int

    @classmethod
    def parse(cls, s: str) -> Self:
        if s.startswith("#") and len(s) >= 7:
            return cls(r=int(s[1:3], 16), g=int(s[3:5], 16), b=int(s[5:7], 16))


def color_palette(start: RGB, end: RGB, length: int) -> list[RGB]:
    step_r = (end.r - start.r) / (length - 1)
    step_g = (end.g - start.g) / (length - 1)
    step_b = (end.b - start.b) / (length - 1)

    palette: list[RGB] = []

    for i in range(length):
        palette.append(
            RGB(
                r=int(start.r + i * step_r),
                g=int(start.g + i * step_g),
                b=int(start.b + i * step_b),
            )
        )

    return palette


COLOR_BASE_INDEX = 10
FADE_LENGTH = 15


def init_fade_out_palette(start: RGB, end: RGB, length: int) -> None:
    for i, color in enumerate(color_palette(start, end, length)):
        curses.init_color(COLOR_BASE_INDEX + i, *_color_to_curses(color))
        curses.init_pair(COLOR_BASE_INDEX + i, COLOR_BASE_INDEX + i, curses.COLOR_BLACK)


def _color_to_curses(rgb: RGB) -> tuple[int, int, int]:
    factor = 1000 / 255
    return int(rgb.r * factor), int(rgb.g * factor), int(rgb.b * factor)


def clear_rect(win: curses.window, rect: Rect, attr: int = 0):
    """Fill a rectangular area with spaces."""
    blank = " " * rect.width
    for i in range(rect.height):
        win.addstr(rect.y + i, rect.x, blank, attr)


def clamp_width(cols: int, perc: float, min_width: int) -> int:
    return min(cols, max(int(perc * cols), min_width))


@contextmanager
def show_cursor():
    try:
        curses.curs_set(1)
        yield
    finally:
        curses.curs_set(0)


def hide_cursor(func):
    @wraps(func)
    def wrapper_func(win: curses.window, *args, **kwargs):
        curses.curs_set(0)
        try:
            return func(win, *args, **kwargs)
        finally:
            curses.curs_set(1)

    return wrapper_func


def split_text_into_lines(text: str, width: int) -> list[str]:
    assert width > 0

    lines: list[str] = []
    cur = 0
    while cur + width < len(text):
        last_space_idx = text[cur : cur + width].rfind(" ")
        if last_space_idx == -1:
            lines.append(text[cur : cur + width])
            cur += width
        elif last_space_idx == 0:
            cur += 1
        else:
            lines.append(text[cur : cur + last_space_idx])
            cur += last_space_idx + 1
    if cur < len(text):
        lines.append(text[cur:])
    return lines


def truncate(s: str, max_length: int, suffix: str = ELLIPSIS) -> str:
    if len(s) <= max_length:
        return s
    assert max_length - len(suffix)
    return s[: max_length - len(suffix)] + suffix
