import curses
import logging

from src.tui.components import draw_border
from src.tui.event import (
    Accepted,
    Cancelled,
    TextfieldEvent,
)
from src.tui.layout import Point, Rect
from src.tui.ui import Id, UIContext
from src.tui.utils import (
    KEY_ESC,
    split_text_into_lines,
)


def textfield(
    ctx: UIContext, id: Id, rect: Rect, title: str = ""
) -> tuple[str, TextfieldEvent | None]:
    assert ctx.layout is not None

    if ctx.uistate.active_id is None:
        ctx.uistate.active_id = id

    event: TextfieldEvent | None = None
    textfield_str = ctx.uistate.textfield_str

    input_width = rect.width - 4
    lines, _ = split_text_into_lines(text=textfield_str, width=input_width)

    cursor_idx = ctx.uistate.textfield_cursor_index
    if cursor_idx is None:
        if len(lines) == 0:
            cursor_idx = 0
        else:
            cursor_idx = len(lines[:-1]) * input_width + len(lines[-1])
        logging.info(f"{cursor_idx=}")

    logging.info(f"{cursor_idx=}")

    cursor = _idx_to_cursor(cursor_idx, lines, width=input_width)
    logging.info(f"{cursor=}")

    _draw_textfield(ctx.stdscr, rect=rect, lines=lines, title=title, cursor=cursor)

    if ctx.uistate.active_id == id and not ctx.uistate.key_consumed:
        key = ctx.uistate.key
        if 32 <= key <= 126:
            textfield_str += chr(key)
            cursor_idx += 1
        elif key == curses.KEY_BACKSPACE and len(textfield_str) > 0:
            textfield_str = textfield_str[:-1]
            cursor_idx -= 1
        elif key == KEY_ESC:
            event = Cancelled()
        elif key == ord("\n"):
            event = Accepted() if len(textfield_str) > 0 else Cancelled()

    ctx.uistate.textfield_cursor_index = cursor_idx
    return textfield_str, event


def _draw_textfield(
    stdscr: curses.window,
    rect: Rect,
    lines: list[str],
    cursor: Point,
    title: str = "",
) -> None:
    draw_border(stdscr, rect=rect, title=title, rounded=True, border_color=1)
    _, _, y, x = rect

    y_start = y + 1
    x_start = x + 2

    for row, line in enumerate(lines):
        stdscr.addstr(y_start + row, x_start, line)

    stdscr.chgat(y_start + cursor.y, x_start + cursor.x, 1, curses.A_REVERSE)


def _idx_to_cursor(idx: int, lines: list[str], width: int) -> Point:
    cursor = Point()

    for i, line in enumerate(lines):
        idx -= len(line)
        if i < len(lines) - 1 and len(line) != width:
            idx -= 1
        if idx > 0:
            cursor.y += 1
        elif idx < 0:
            cursor.x = -idx
        else:
            cursor.x = len(line)

    return cursor


# def _idx_to_cursor(idx: int, lines: list[str]) -> Point:
#     if idx == 0:
#         return Point()
#
#     cursor = Point()
#     i = 0
#     for row, line in enumerate(lines):
#         for ch in line:
#             if i == idx:
#                 return cursor
#             cursor.x += 1
#             i += 1
#         if row < len(lines) - 1:
#             cursor.y += 1
#             cursor.x = 0
#             if len(line) < 5:
#                 cursor.x += 1
#     return cursor
#
