import _curses
import curses
from contextlib import suppress

from src.tui.data import Board
from src.tui.layout import Layout, Rect
from src.tui.utils import ELLIPSIS


def box(
    rect: Rect,
    title: str,
    content: list[str],
    selected: int,
    highlighted: bool = False,
):
    height, width, y, x = rect
    win = curses.newwin(height, width, y, x)

    # Draw Border
    color = curses.color_pair(1) if highlighted else curses.color_pair(0)
    win.addch(0, 0, curses.ACS_ULCORNER, color)
    win.hline(0, 1, curses.ACS_HLINE, width - 2, color)
    win.addch(0, width - 1, curses.ACS_URCORNER, color)

    for y in range(1, height + 1):
        with suppress(_curses.error):
            win.addch(y, 0, curses.ACS_VLINE, color)
            win.addch(y, width - 1, curses.ACS_VLINE, color)

    win.addch(height - 1, 0, curses.ACS_LLCORNER, color)
    win.hline(height - 1, 1, curses.ACS_HLINE, width - 2, color)
    with suppress(_curses.error):
        win.addch(height - 1, width - 1, curses.ACS_LRCORNER, color)

    # Draw Content
    if len(title) > width:
        title = title[: width - 1] + ELLIPSIS

    if width > 4:
        win.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        for i, line in enumerate(content):
            if len(line) > width - 4:
                line = line[: width - 4 - 1] + ELLIPSIS
            with suppress(_curses.error):
                win.addstr(i + 1, 2, line)
            if highlighted:
                if i == selected:
                    win.chgat(i + 1, 1, width - 2, curses.color_pair(2))
    win.refresh()


def text(rect: Rect, s: str, attr: int = 0, centered: bool = True) -> None:
    height, width, y, x = rect
    height = height if height is not None else 1
    win = curses.newwin(height, width, y, x)
    win.bkgd(" ", curses.color_pair(3))

    if len(s) > width:
        s = s[: width - 1] + ELLIPSIS

    start_x = width // 2 - len(s) // 2 if centered else 0
    with suppress(_curses.error):
        win.addstr(0, start_x, s, attr)

    win.refresh()
