import _curses
import curses
from contextlib import suppress

from src.tui.data import Event, Id, UIContext
from src.tui.layout import Rect
from src.tui.utils import (
    ELLIPSIS,
    HORIZONTAL_BAR,
    KEY_ESC,
    ROUNDED_BOTTOMLEFT,
    ROUNDED_BOTTOMRIGHT,
    ROUNDED_TOPLEFT,
    ROUNDED_TOPRIGHT,
    VERTICAL_BAR,
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
        stdscr.addstr(y, x + (width - len(title)) // 2, title, curses.A_BOLD)

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

    height, width, y, x = rect
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


def text(
    stdscr: curses.window, rect: Rect, s: str, attr: int = 0, centered: bool = True
) -> None:
    height, width, y, x = rect

    if len(s) > width:
        s = s[: width - 1] + ELLIPSIS

    attr |= curses.color_pair(3)

    for row in range(height):
        with suppress(_curses.error):
            stdscr.addstr(y + row, x, " " * width, curses.color_pair(3))

    start_x = width // 2 - len(s) // 2 if centered else 0
    with suppress(_curses.error):
        stdscr.addstr(y, start_x, s, attr)


def text_field(ctx: UIContext, id: Id, width: int) -> tuple[str, Event]:
    assert ctx.layout is not None

    res: Event = "Continue"
    textfield_str = ctx.uistate.textfield_str

    with ctx.layout.horizontal(
        columns=1,
        child_min_width=10,
        screen_padding=ctx.layout.cols // 2 - width // 2,
    ) as ok:
        if ok:
            lines = split_text_into_lines(text=textfield_str, width=width - 4)
            rect = ctx.layout.next_rect(height=max(1, len(lines)) + 2)

            _draw_textfield(ctx.stdscr, rect, lines, title=str(ctx.event_type))

            if ctx.uistate.active_id == id and not ctx.uistate.key_consumed:
                key = ctx.uistate.key
                if 32 <= key <= 126:
                    textfield_str += chr(key)
                elif key == curses.KEY_BACKSPACE and len(textfield_str) > 0:
                    textfield_str = textfield_str[:-1]
                elif key == KEY_ESC:
                    res = "Cancelled"
                elif key == ord("\n"):
                    res = "Accepted"

    return textfield_str, res


def _draw_textfield(
    stdscr: curses.window, rect: Rect, lines: list[str], title: str = ""
) -> None:
    height, width, y, x = rect
    stdscr.addstr(
        y, x, f"{ROUNDED_TOPLEFT}{HORIZONTAL_BAR * (width - 2)}{ROUNDED_TOPRIGHT}"
    )
    stdscr.addstr(
        y + height - 1,
        x,
        f"{ROUNDED_BOTTOMLEFT}{HORIZONTAL_BAR * (width - 2)}{ROUNDED_BOTTOMRIGHT}",
    )

    if title:
        if len(title) > width:
            title = title[: width - 1] + ELLIPSIS
        x_offset = width // 2 - len(title) // 2
        stdscr.addstr(y, x + x_offset, title)
    for row in range(1, height - 1):
        stdscr.addstr(y + row, x, VERTICAL_BAR)
        stdscr.addstr(y + row, x + width - 1, VERTICAL_BAR)

        for row, line in enumerate(lines):
            stdscr.addstr(y + row + 1, x + 2, line)

            x_offset = len(lines[-1]) if lines else 0
            y_offset = len(lines) if lines else 1
            stdscr.addstr(y + y_offset, x + x_offset + 2, "█")
