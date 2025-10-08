import _curses
import curses
from contextlib import suppress

from src.tui.event import (
    Event,
    HideHover,
)
from src.tui.layout import Rect
from src.tui.ui import UIContext
from src.tui.utils import (
    ELLIPSIS,
    clear_rect,
    split_text_into_lines,
)


def draw_border(
    stdscr: curses.window,
    rect: Rect,
    title: str,
    border_color: int = 0,
    *,
    rounded: bool,
) -> None:
    upper_left_corner = "╭" if rounded else "┌"
    upper_right_corner = "╮" if rounded else "┐"
    lower_left_corner = "╰" if rounded else "└"
    lower_right_corner = "╯" if rounded else "┘"
    color = curses.color_pair(border_color)

    height, width, y, x = rect

    stdscr.addch(y, x, upper_left_corner, color)
    stdscr.addstr(y, x + 1, "─" * (width - 2), color)
    stdscr.addch(y, x + width - 1, upper_right_corner, color)

    if title:
        if len(title) > width:
            title = title[: width - 1] + ELLIPSIS
        stdscr.addstr(y, x + (width - len(title)) // 2, title, curses.A_BOLD | color)

    for row in range(1, height - 1):
        with suppress(_curses.error):
            stdscr.addch(y + row, x, "│", color)
            stdscr.addch(y + row, x + width - 1, "│", color)

    stdscr.addch(y + height - 1, x, lower_left_corner, color)
    stdscr.addstr(y + height - 1, x + 1, "─" * (width - 2), color)
    with suppress(_curses.error):
        stdscr.addch(y + height - 1, x + width - 1, lower_right_corner, color)


def box(
    stdscr: curses.window,
    rect: Rect,
    lines: list[str],
    selected: int = -1,
    title: str = "",
    padding: int = 1,
    *,
    highlighted: bool = False,
    rounded: bool = False,
    squash: bool = True,
):
    draw_border(
        stdscr=stdscr,
        rect=rect,
        title=title,
        border_color=1 if highlighted else 0,
        rounded=rounded,
    )

    _, width, y, x = rect
    y += 1
    x += 1 + padding

    if width > 4:
        for row, line in enumerate(lines):
            if squash and len(line) > width - 4:
                line = line[: width - 4 - padding] + ELLIPSIS
            with suppress(_curses.error):
                stdscr.addstr(y + row, x, line)
            if highlighted:
                if row == selected:
                    stdscr.chgat(
                        y + row,
                        x - padding,
                        width - 2,  # border(2)
                        curses.color_pair(2),
                    )


def multiline(
    stdscr: curses.window,
    rect: Rect,
    lines: list[str],
    fg_attr: int = 0,
    padding_attr: int = 0,
    *,
    centered: bool,
) -> None:
    height, width, y, x = rect

    for row in range(height):
        stdscr.chgat(y + row, x, width, padding_attr)

    for row, line in enumerate(lines):
        x_offset = (width - len(line)) // 2 if centered else 0
        with suppress(_curses.error):
            stdscr.addstr(y + row, x + x_offset, line, fg_attr)


def text(
    stdscr: curses.window,
    rect: Rect,
    msg: str,
    fg_attr: int = 0,
    padding_attr: int = 0,
    *,
    centered: bool,
) -> None:
    height, width, y, x = rect

    if len(msg) > width:
        msg = msg[: width - 1] + ELLIPSIS

    for row in range(height):
        stdscr.chgat(y + row, x, width, padding_attr)

    x_offset = width // 2 - len(msg) // 2 if centered else 0
    with suppress(_curses.error):
        stdscr.addstr(y, x + x_offset, msg, fg_attr)


def hover(ctx: UIContext, width: int) -> Event | None:
    assert ctx.uistate.cursor_pos is not None

    lines = split_text_into_lines(text=ctx.uistate.hover_text, width=width)
    popup_width = max(map(len, lines)) + 4
    popup_height = len(lines) + 2
    popup_y = ctx.uistate.cursor_pos.y - len(lines) - 2
    popup_x = ctx.uistate.cursor_pos.x - 1

    if popup_x + popup_width > ctx.cols:
        popup_x += ctx.cols - (popup_x + popup_width)
    if popup_y < 0:
        popup_y = ctx.uistate.cursor_pos.y + 1

    rect = Rect(height=popup_height, width=popup_width, y=popup_y, x=popup_x)
    clear_rect(ctx.stdscr, rect)
    box(ctx.stdscr, rect=rect, lines=lines, rounded=True)

    key = ctx.uistate.key
    if key == -1:
        return None

    return HideHover()


def status(ctx: UIContext, msg: str, pair_number: int) -> None:
    if len(msg) > ctx.cols:
        lines = split_text_into_lines(text=msg, width=ctx.cols)
        rect = Rect(height=len(lines), width=ctx.cols, y=ctx.rows - len(lines), x=0)
        multiline(
            ctx.stdscr,
            rect=rect,
            lines=lines,
            fg_attr=curses.color_pair(pair_number) | curses.A_REVERSE,
            centered=True,
        )
    else:
        rect = Rect(height=1, width=ctx.cols, y=ctx.rows - 1, x=0)
        text(
            ctx.stdscr,
            rect=rect,
            msg=msg,
            fg_attr=curses.color_pair(pair_number) | curses.A_REVERSE,
            centered=True,
        )
