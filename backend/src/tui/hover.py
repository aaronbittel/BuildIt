from src.tui.components import box
from src.tui.data import Event, UIContext
from src.tui.layout import Rect
from src.tui.utils import clear_rect, split_text_into_lines


def hover(ctx: UIContext, width: int) -> Event | None:
    assert ctx.uistate.cursor_position is not None

    lines = split_text_into_lines(text=ctx.uistate.hover_text, width=width)
    popup_width = max(map(len, lines)) + 4
    popup_height = len(lines) + 2
    popup_y = ctx.uistate.cursor_position.y - len(lines) - 2
    popup_x = ctx.uistate.cursor_position.x - 1

    if popup_x + popup_width > ctx.cols:
        popup_x += ctx.cols - (popup_x + popup_width)
    if popup_y < 0:
        popup_y = ctx.uistate.cursor_position.y + 1

    rect = Rect(height=popup_height, width=popup_width, y=popup_y, x=popup_x)
    clear_rect(ctx.stdscr, rect)
    box(ctx.stdscr, rect=rect, lines=lines, rounded=True)

    key = ctx.uistate.key
    if key == -1:
        return None

    return "Hide Hover"
