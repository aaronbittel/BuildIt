from __future__ import annotations

import curses
import logging

from src.tui import ui
from src.tui.app import App
from src.tui.board import Board, Stage, Task
from src.tui.components import (
    board_widget,
    display_title,
    hover,
    status,
    textfield,
)
from src.tui.event import (
    Accepted,
    AddStage,
    AddTask,
    Cancelled,
    Continue,
    EditStage,
    EditTask,
    HideHover,
    Quit,
    ShowHover,
    ShowStatusMessage,
    UpdateBoard,
)
from src.tui.layout import Layout
from src.tui.storage import DATA_PATH, __load_state_imm, convert_imm_boards_to_boards
from src.tui.ui import UIContext, UiState, widget_id
from src.tui.utils import (
    FADE_LENGTH,
    RGB,
    _color_to_curses,
    clamp_width,
    color_palette,
    init_fade_out_palette,
)

# TODO: Manuall switching between vertical and horizontal layout for board
# TODO: saving and loading board to db + menu
# TODO: Switch between blocking (normal board) and non-blocking (text input) mode

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


USE_PREFILLED_DATA = True
FPS = 30


if not USE_PREFILLED_DATA:
    DATA_PATH.mkdir(exist_ok=True)


def main(stdscr: curses.window) -> None:
    curses.set_escdelay(25)
    curses.start_color()
    # curses.use_default_colors() ?
    # TODO: Handle if this is not possible
    assert curses.can_change_color(), "Terminal cannot redefine colors"

    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.curs_set(0)

    if USE_PREFILLED_DATA:
        stages = [
            Stage(
                "Backlog",
                tasks=[Task("Todo 1"), Task("Todo 2")],
            ),
            Stage(
                "In Progress", tasks=[Task("Task 1"), Task("Task 2"), Task("Task 3")]
            ),
            Stage(
                "Done",
                tasks=[
                    Task(
                        "A really really long Message to Display. A really really long Message to Display. A really really long Message to Display."
                    ),
                    Task("Done 1"),
                    Task("Done 2"),
                    Task("Done 3"),
                ],
            ),
        ]
        board = Board(title="Main Board", stages=stages)
    else:
        imm_boards = __load_state_imm("25_10_02-11_39_32")
        board = convert_imm_boards_to_boards(imm_boards)

    rows, cols = stdscr.getmaxyx()

    init_fade_out_palette(
        start=RGB(220, 220, 220), end=RGB.parse("#1D1F21"), length=FADE_LENGTH
    )
    uistate = UiState()
    app = App(board)
    ctx = UIContext(stdscr=stdscr, rows=rows, cols=cols, uistate=uistate)

    stdscr.refresh()
    stdscr.timeout(int(1 / FPS * 1000))

    board_id = widget_id("board")
    textfield_id = widget_id("textfield")

    logging.info(f"{rows=} {cols=}")

    while app.running:
        ctx.uistate.key = stdscr.getch()
        ctx.uistate.key_consumed = False
        events: list[Event] = []

        if ctx.uistate.active_id != textfield_id and ctx.uistate.key == ord("q"):
            events.append(Quit())
            ctx.uistate.key_consumed = True

        if ctx.uistate.key == curses.KEY_RESIZE:
            ctx.rows, ctx.cols = stdscr.getmaxyx()
            logging.info(f"rows={ctx.rows} cols={ctx.cols}")
            ctx.uistate.key_consumed = True
            continue

        stdscr.erase()

        with Layout(ctx.rows, ctx.cols) as layout:
            ctx.layout = layout

            display_title(ctx, title=app.board.title)

            board_event = board_widget(
                ctx, board=app.board, id=board_id, stage_min_width=25
            )
            if board_event is not None:
                events.append(board_event)

            if ctx.uistate.textfield_open:
                width = clamp_width(ctx.cols, perc=0.75, min_width=25)
                ctx.uistate.textfield_str, res = textfield(
                    ctx,
                    id=textfield_id,
                    width=width,
                )
                events.append(res)

        if ctx.uistate.hover_open:
            width = clamp_width(ctx.cols, perc=0.6, min_width=25)
            hover_event = hover(ctx, width=width)
            if hover_event:
                events.append(hover_event)

        if (
            ctx.uistate.status_message
            and (pair_number := ctx.uistate.status_message_color()) is not None
        ):
            status(
                ctx,
                msg=ctx.uistate.status_message,
                pair_number=pair_number,
            )

        for event in events:
            if event:
                logging.info(f"{event=}")
            match event:
                case AddTask() as add_task_event:
                    app.open_textfield(
                        ctx, event_type=add_task_event, textfield_id=textfield_id
                    )
                case EditTask(prefill=text_to_edit) as edit_task_event:
                    app.open_textfield(
                        ctx,
                        event_type=edit_task_event,
                        textfield_id=textfield_id,
                        initial_text=text_to_edit,
                    )
                case AddStage() as add_stage_event:
                    app.open_textfield(
                        ctx, event_type=add_stage_event, textfield_id=textfield_id
                    )
                case EditStage(prefill=text_to_edit) as edit_stage_event:
                    app.open_textfield(
                        ctx,
                        event_type=edit_stage_event,
                        textfield_id=textfield_id,
                        initial_text=text_to_edit,
                    )
                case Continue():
                    pass
                case Accepted():
                    app.handle_accept_textfield(ctx)
                case Cancelled():
                    app.handle_cancel_textfield(ctx)
                case UpdateBoard(new_board=new_board):
                    app.board = new_board
                case ShowHover(position=cursor_pos, text=text_to_show):
                    ctx.uistate.cursor_pos = cursor_pos
                    ctx.uistate.hover_open = True
                    ctx.uistate.hover_text = text_to_show
                case HideHover():
                    ctx.uistate.cursor_pos = None
                    ctx.uistate.hover_open = False
                case ShowStatusMessage(text=msg):
                    ctx.uistate.init_status_message(msg=msg, duration=4.0)
                case Quit():
                    app.running = False
                case e:
                    logging.error("Unmatched event: %s", e)
                    assert False, "unreachable"

        stdscr.noutrefresh()
        curses.doupdate()


if __name__ == "__main__":
    curses.wrapper(main)
