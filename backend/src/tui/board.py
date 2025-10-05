import curses

from src.tui.components import box
from src.tui.data import Board, Event, Id, UIContext
from src.tui.layout import Layout, Rect
from src.tui.utils import KEY_ESC


def board_widget(
    ctx: UIContext, board: Board, id: Id, stage_min_width: int
) -> Event | None:
    if ctx.uistate.active_id is None:
        ctx.uistate.active_id = id

    if len(board.stages) > 0:
        with ctx.layout.horizontal(
            screen_padding=1,
            spacing=2,
            after_spacing=1,
            child_min_width=stage_min_width,
            columns=len(board.stages),
        ) as h_ok:
            if h_ok:
                board_rects = _board_view(ctx.stdscr, ctx.layout, board)
                board_is_showing = True

            if not h_ok:
                with ctx.layout.vertical(
                    screen_padding=1,
                    spacing=0,
                    child_min_width=stage_min_width,
                    rows=len(board.stages),
                ) as v_ok:
                    if v_ok:
                        board_rects = _board_view(ctx.stdscr, ctx.layout, board)
                    board_is_showing = v_ok

    event: Event = None

    if ctx.uistate.active_id == id and not ctx.uistate.key_consumed:
        ctx.uistate.key_consumed = True
        key = ctx.uistate.key
        if key == ord("j"):
            board.stage.next_task()
        elif key == ord("k"):
            board.stage.prev_task()
        elif key == ord("n"):
            board.forward_task()
        elif key == ord("p"):
            board.recall_task()
        elif key == ord("a"):
            event = "Add Task"
        elif key == ord("e"):
            if len(board.stage) > 0:
                event = ("Edit Task", {"prefill": board.stage.task.name})
            else:
                event = "Add Task"
        elif key == ord("x"):
            if len(board.stage) > 0:
                board.stage.pop()
        elif key == ord("s"):
            if (
                len(board.stage) > 0
                and board_is_showing
                and board_rects[board.selected].width - 4 < len(board.stage.task.name)
            ):
                event = ("Hover Task", {"position": board_rects[board.selected]})
        elif key == ord("J"):
            board.stage.move_task(1)
        elif key == ord("K"):
            board.stage.move_task(-1)
        elif key == ord("A"):
            event = "Add Stage"
        elif key == ord("E"):
            event = ("Edit Stage", {"prefill": board.stage.title})
        elif key == ord("X"):
            # TODO: Add confirmation
            if len(board.stages) > 0:
                board.stages.pop(board.selected)
                if board.selected >= len(board.stages):
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
        elif key == KEY_ESC:
            board = board.goto_prev_board()
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
