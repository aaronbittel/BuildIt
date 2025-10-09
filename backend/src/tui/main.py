from __future__ import annotations

import curses
import logging
import os
from pathlib import Path

from src.tui.app import App
from src.tui.board_ui import board_widget
from src.tui.components import (
    hover,
    status,
    text,
)
from src.tui.event import (
    Accepted,
    AddStage,
    AddTask,
    Cancelled,
    CreateNewBoard,
    EditStage,
    EditTask,
    Event,
    HideHover,
    Quit,
    ShowHover,
    ShowStatusMessage,
    SwitchBoard,
)
from src.tui.layout import Layout
from src.tui.sqlite import SqliteStorage
from src.tui.storage import DummyStorage, Storage
from src.tui.textfield import textfield
from src.tui.ui import UIContext, UiState, widget_id
from src.tui.utils import (
    FADE_LENGTH,
    RGB,
    clamp_width,
    init_fade_out_palette,
)

# TODO: Manuall switching between vertical and horizontal layout for board
# TODO: saving and loading board to db + menu

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


FPS = 30


def display_title(ctx: UIContext, title: str) -> None:
    assert ctx.layout is not None
    with ctx.layout.vertical(rows=1, after_spacing=1) as ok:
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


DB_PATH = Path("./dbs")


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

    path_str = os.getenv("BUILDIT_STORAGE")
    storage: Storage | None = None
    if path_str is None:
        storage = DummyStorage()
    else:
        path = DB_PATH / f"{path_str}.db"
        path = path if path.exists() else DB_PATH / "dump.db"
        logging.info("LOADING DB: %s", path)
        storage = SqliteStorage(path)

    board = storage.load_board()

    rows, cols = stdscr.getmaxyx()

    init_fade_out_palette(
        start=RGB(220, 220, 220), end=RGB.parse("#1D1F21"), length=FADE_LENGTH
    )
    uistate = UiState()
    app = App(board, storage=storage)
    ctx = UIContext(stdscr=stdscr, rows=rows, cols=cols, uistate=uistate)

    stdscr.refresh()
    stdscr.timeout(int(1 / FPS * 1000))

    board_id = widget_id("board")
    textfield_id = widget_id("textfield")

    logging.info(f"{rows=} {cols=}")

    while app.running:
        ctx.uistate.key = stdscr.getch()
        ctx.uistate.key_consumed = False
        # NOTE: move events in UIContext?
        events: list[Event] = []

        stdscr.erase()

        if ctx.uistate.active_id != textfield_id and ctx.uistate.key == ord("q"):
            events.append(Quit())
            ctx.uistate.key_consumed = True

        if ctx.uistate.key == curses.KEY_RESIZE:
            ctx.rows, ctx.cols = stdscr.getmaxyx()
            logging.info(f"rows={ctx.rows} cols={ctx.cols}")
            ctx.uistate.key_consumed = True
            continue

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
                assert ctx.board_event is not None
                ctx.uistate.textfield_str, textfield_event = textfield(
                    ctx,
                    title=ctx.board_event.title,
                    id=textfield_id,
                    width=width,
                )
                if textfield_event:
                    events.append(textfield_event)

        if ctx.uistate.hover_open:
            width = clamp_width(ctx.cols, perc=0.6, min_width=25)
            hover_event = hover(ctx, width=width)
            if hover_event:
                events.append(hover_event)

        if (
            ctx.uistate.status_message is not None
            and (pair_number := ctx.uistate.status_message_color()) is not None
        ):
            status(
                ctx,
                msg=ctx.uistate.status_message.msg,
                pair_number=pair_number,
            )

        for event in events:
            logging.info("%s", event)
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
                case Accepted():
                    app.handle_accept_textfield(ctx)
                case Cancelled():
                    app.handle_cancel_textfield(ctx)
                case CreateNewBoard(new_board=new_board):
                    app.board = new_board
                case SwitchBoard(board=board):
                    app.board = board
                case ShowHover(position=cursor_pos, text=text_to_show):
                    ctx.uistate.cursor_pos = cursor_pos
                    ctx.uistate.hover_open = True
                    ctx.uistate.hover_text = text_to_show
                case HideHover():
                    ctx.uistate.cursor_pos = None
                    ctx.uistate.hover_open = False
                case ShowStatusMessage(text=msg, duration=duration):
                    ctx.uistate.init_status_message(msg=msg, duration=duration)
                case Quit():
                    app.running = False
                    app.storage.save_board(app.board)
                case e:
                    logging.error("Unmatched event: %s", e)
                    assert False, "unreachable"

        stdscr.noutrefresh()
        curses.doupdate()


if __name__ == "__main__":
    curses.wrapper(main)
