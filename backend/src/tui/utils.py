from contextlib import contextmanager, suppress
import curses
from curses import textpad
import _curses
from functools import wraps
import logging
from pathlib import Path

ROUNDED_TOPLEFT = "╭"
ROUNDED_TOPRIGHT = "╮"
ROUNDED_BOTTOMRIGHT = "╯"
ROUNDED_BOTTOMLEFT = "╰"
VERTICAL_BAR = "│"
HORIZONTAL_BAR = "─"
ELLIPSIS = "…"

KEY_EXIT = 7
KEY_IGNORE = 0


def border(win: curses.window, title: str | None = None) -> curses.window:
    org_height, org_width = win.getmaxyx()
    org_y, org_x = win.getbegyx()

    height, width = org_height + 2, org_width + 2
    border_win = curses.newwin(height, width, org_y - 1, org_x - 1)

    border_win.addstr(
        0, 0, ROUNDED_TOPLEFT + HORIZONTAL_BAR * (width - 2) + ROUNDED_TOPRIGHT
    )

    for i in range(height - 2):
        border_win.addstr(i + 1, 0, VERTICAL_BAR)
        border_win.addstr(i + 1, width - 1, VERTICAL_BAR)
    border_win.addstr(height - 1, 0, ROUNDED_BOTTOMLEFT)
    border_win.addstr(height - 1, 1, HORIZONTAL_BAR * (width - 2))

    with suppress(_curses.error):
        border_win.addstr(
            height - 1,
            0,
            ROUNDED_BOTTOMLEFT + HORIZONTAL_BAR * (width - 2) + ROUNDED_BOTTOMRIGHT,
        )

    if title:
        border_win.addstr(0, 2, title)
    border_win.refresh()
    return border_win


def get_input(
    y: int,
    x: int,
    width: int,
    height: int = 1,
    text: str | None = None,
    title: str | None = None,
) -> str:
    def validator(ch: int) -> int:
        if ch == ord("\n") or ch == curses.KEY_RESIZE:
            return KEY_EXIT
        return ch

    if (text is not None and width < len(text)) or width < 4:
        return ""

    edit_win = curses.newwin(height, width, y, x)
    if text is not None:
        edit_win.addstr(0, 0, text)

    border_win = border(edit_win, title=title)
    textbox = textpad.Textbox(edit_win, insert_mode=True)

    with show_cursor():
        text = textbox.edit(validator).strip()

    border_win.clear()
    edit_win.clear()
    border_win.refresh()
    edit_win.refresh()
    return text


def title(win: curses.window, cols: int, text: str) -> None:
    win.move(0, 0)
    win.clrtoeol()
    win.refresh()

    if cols <= 1:
        return

    if cols < len(text):
        text = text[: cols - 1] + ELLIPSIS
    win.addstr(0, cols // 2 - len(text) // 2, text, curses.A_BOLD | curses.A_UNDERLINE)


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
