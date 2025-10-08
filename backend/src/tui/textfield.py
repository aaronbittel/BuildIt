import curses

from src.tui.event import (
    Accepted,
    Cancelled,
    TextfieldEvent,
)
from src.tui.layout import Rect
from src.tui.ui import Id, UIContext
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


def textfield(ctx: UIContext, id: Id, width: int) -> tuple[str, TextfieldEvent | None]:
    assert ctx.layout is not None

    event: TextfieldEvent | None = None
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
                    event = Cancelled()
                elif key == ord("\n"):
                    event = Accepted() if len(textfield_str) > 0 else Cancelled()

    return textfield_str, event


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
