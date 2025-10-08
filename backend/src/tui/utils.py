import curses
from contextlib import contextmanager
from functools import wraps

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
