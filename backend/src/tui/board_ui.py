import curses

from src.tui.board import Board
from src.tui.components import box
from src.tui.event import (
    AddStage,
    AddTask,
    EditStage,
    EditTask,
    Event,
    ShowHover,
    ShowStatusMessage,
    UpdateBoard,
)
from src.tui.layout import Layout, Point, Rect
from src.tui.ui import Id, UIContext
from src.tui.utils import (
    KEY_ESC,
)


def board_widget(
    ctx: UIContext, board: Board, id: Id, stage_min_width: int
) -> Event | None:
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

    event: Event | None = None

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
