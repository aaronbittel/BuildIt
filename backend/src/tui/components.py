import _curses
import curses
import logging
from contextlib import suppress

from src.tui.board import Board
from src.tui.event import (
    Accepted,
    AddStage,
    AddTask,
    AppEvent,
    Cancelled,
    Continue,
    EditStage,
    EditTask,
    HideHover,
    ShowHover,
    ShowStatusMessage,
    TextfieldEvent,
    UpdateBoard,
)
from src.tui.layout import Layout, Point, Rect
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
    clear_rect,
    split_text_into_lines,
)


def board_widget(
    ctx: UIContext, board: Board, id: Id, stage_min_width: int
) -> AppEvent | None:
    assert ctx.layout is not None

    if ctx.uistate.active_id is None:
        ctx.uistate.active_id = id

    if len(board) > 0:
        with ctx.layout.horizontal(
            screen_padding=1,
            spacing=2,
            after_spacing=1,
            child_min_width=stage_min_width,
            columns=len(board),
        ) as h_ok:
            if h_ok:
                board_rects = _board_view(ctx.stdscr, ctx.layout, board)
                board_is_showing = True

            if not h_ok:
                with ctx.layout.vertical(
                    screen_padding=1,
                    spacing=0,
                    child_min_width=stage_min_width,
                    rows=len(board),
                ) as v_ok:
                    if v_ok:
                        board_rects = _board_view(ctx.stdscr, ctx.layout, board)
                    board_is_showing = v_ok

    event: AppEvent | None = None

    key = ctx.uistate.key
    if ctx.uistate.active_id == id and not ctx.uistate.key_consumed and key != -1:
        ctx.uistate.key_consumed = True
        if key == ord("j"):
            if len(board) > 0:
                board.stage.next_task()
        elif key == ord("k"):
            if len(board) > 0:
                board.stage.prev_task()
        elif key == ord("n"):
            if len(board) > 0:
                board.forward_task()
        elif key == ord("p"):
            board.recall_task()
        elif key == ord("a"):
            if len(board) > 0:
                event = AddTask()
        elif key == ord("e"):
            if len(board) > 0:
                if len(board.stage.tasks) > 0:
                    event = EditTask(prefill=board.stage.task.name)
                else:
                    event = AddTask()
        elif key == ord("x"):
            if len(board) > 0 and len(board.stage) > 0:
                board.stage.pop()
        elif key == ord("s"):
            if (
                len(board) > 0
                and len(board.stage) > 0
                and board_is_showing
                and board_rects[board.selected].width - 4 < len(board.stage.task.name)
            ):
                rect = board_rects[board.selected]
                y_offset = board.stage.selected
                # fmt: off
                event = ShowHover(
                    position=Point(
                        y=rect.y + 1 + y_offset, # border(1)
                        x=rect.x + 2,            # border(1) + padding(1)
                    ),
                    text=board.stage.task.name,
                )
                # fmt: on
        elif key == ord("J"):
            if len(board) > 0:
                board.stage.move_task(1)
        elif key == ord("K"):
            if len(board) > 0:
                board.stage.move_task(-1)
        elif key == ord("A"):
            event = AddStage()
        elif key == ord("E"):
            if len(board) > 0:
                event = EditStage(prefill=board.stage.title)
            else:
                event = AddStage()
        elif key == ord("X"):
            # TODO: Add confirmation
            if len(board) > 0:
                board.stages.pop(board.selected)
                if board.selected >= len(board):
                    board.selected -= 1
        elif key == ord("\t"):
            board.next()
        elif key == curses.KEY_BTAB:
            board.prev()
        elif key == ord("\n"):
            if len(board.stage) > 0:
                board = board.goto_next_board(
                    stage_idx=board.selected,
                    task_idx=board.stage.selected,
                    prefilled=False,
                )
                event = UpdateBoard(new_board=board)
        elif key == KEY_ESC:
            board = board.goto_prev_board()
            event = UpdateBoard(new_board=board)
        elif key == ord("z"):
            event = ShowStatusMessage(text="This is a status message" * 5)
    return event


def _board_view(stdscr: curses.window, layout: Layout, board: Board) -> list[Rect]:
    rects: list[Rect] = []
    for i, stage in enumerate(board.stages):
        content = list(map(lambda t: t.name, stage.tasks))
        rect = layout.next_rect(height=max(len(content) + 2, 5))
        highlighted = i == board.selected
        box(
            stdscr,
            rect=rect,
            title=stage.title,
            lines=content,
            selected=board.stage.selected,
            highlighted=highlighted,
            rounded=False,
        )
        rects.append(rect)
    return rects


def display_title(ctx: UIContext, title: str) -> None:
    assert ctx.layout is not None
    with ctx.layout.vertical(rows=1, after_spacing=1, child_min_width=5) as ok:
        if ok:
            rect = ctx.layout.next_rect(height=1)
            text(
                ctx.stdscr,
                rect,
                title,
                fg_attr=curses.A_BOLD | curses.A_UNDERLINE | curses.color_pair(3),
                padding_attr=curses.color_pair(3),
                centered=True,
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


def textfield(ctx: UIContext, id: Id, width: int) -> tuple[str, TextfieldEvent]:
    assert ctx.layout is not None

    res: TextfieldEvent = Continue()
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
                    res = Cancelled()
                elif key == ord("\n"):
                    res = Accepted() if len(textfield_str) > 0 else Cancelled()

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


def hover(ctx: UIContext, width: int) -> AppEvent | None:
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
