from __future__ import annotations

import curses
import logging

from src.tui.board import board_widget
from src.tui.components import text, text_field
from src.tui.data import (
    DATA_PATH,
    Board,
    EventType,
    Id,
    Stage,
    Task,
    UIContext,
    UiState,
    __load_state_imm,
    convert_imm_boards_to_boards,
    widget_id,
)
from src.tui.hover import hover
from src.tui.layout import Layout

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


class App:
    def __init__(self, board: Board) -> None:
        self.board = board

        self.running = True
        self.filename = ""
        self.choose_file = not USE_PREFILLED_DATA

    def open_textfield(
        self,
        ctx: UIContext,
        event_type: EventType,
        textfield_id: Id,
        initial_text: str = "",
    ) -> None:
        ctx.uistate.textfield_open = True
        ctx.uistate.textfield_str = initial_text
        ctx.event_type = event_type
        ctx.uistate.active_id = textfield_id

    def handle_accept_textfield(self, ctx: UIContext) -> None:
        assert ctx.event_type is not None

        if ctx.event_type == "Add Task":
            self.board.stage.add(Task(name=ctx.uistate.textfield_str))
        elif ctx.event_type == "Edit Task":
            self.board.stage.task.name = ctx.uistate.textfield_str
        elif ctx.event_type == "Add Stage":
            self.board.add_stage(Stage(title=ctx.uistate.textfield_str))
            self.board.selected = len(self.board.stages) - 1
        elif ctx.event_type == "Edit Stage":
            self.board.stage.title = ctx.uistate.textfield_str
        elif ctx.event_type == "Saving":
            pass
        else:
            logging.error("unexpected event: %s", ctx.event_type)
            assert False, "unreachable"

        ctx.event_type = None
        ctx.uistate.textfield_str = ""
        ctx.uistate.textfield_open = False
        ctx.uistate.active_id = None

    def handle_cancel_textfield(self, ctx: UIContext) -> None:
        ctx.uistate.textfield_str = ""
        ctx.uistate.textfield_open = False
        ctx.event_type = None
        ctx.uistate.active_id = None


def display_title(stdscr: curses.window, layout: Layout, title: str) -> None:
    rect = layout.next_rect(height=1)
    text(
        stdscr,
        rect,
        title,
        attr=curses.A_BOLD | curses.A_UNDERLINE,
    )


if not USE_PREFILLED_DATA:
    DATA_PATH.mkdir(exist_ok=True)


def clamp_width(cols: int, perc: float, min_width: int) -> int:
    return min(cols, max(int(perc * cols), min_width))


def main(stdscr: curses.window) -> None:
    curses.set_escdelay(25)
    curses.start_color()
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

    uistate = UiState()
    app = App(board)
    ctx = UIContext(stdscr=stdscr, rows=rows, cols=cols, uistate=uistate)

    stdscr.refresh()
    stdscr.timeout(int(1 / FPS * 1000))

    stage_min_width = 25

    edit_width = clamp_width(cols=cols, perc=0.75, min_width=25)

    board_id = widget_id("board")
    textfield_id = widget_id("textfield")

    logging.info(f"{rows=} {cols=}")

    while app.running:
        ctx.uistate.key = stdscr.getch()
        ctx.uistate.key_consumed = False
        events = []

        if ctx.uistate.active_id != textfield_id and ctx.uistate.key == ord("q"):
            app.running = False
            ctx.uistate.key_consumed = True
            continue

        if ctx.uistate.key == curses.KEY_RESIZE:
            logging.info(f"{rows=} {cols=}")
            ctx.rows, ctx.cols = stdscr.getmaxyx()
            edit_width = calc_edit_width(cols)
            ctx.uistate.key_consumed = True

        stdscr.erase()

        with Layout(stdscr, rows, cols) as layout:
            ctx.layout = layout
            with layout.vertical(rows=1, after_spacing=1, child_min_width=5) as ok:
                if ok:
                    display_title(ctx.stdscr, layout=layout, title=app.board.title)

            board_id = widget_id("board")
            board_event = board_widget(
                ctx,
                board=app.board,
                id=board_id,
                stage_min_width=stage_min_width,
            )
            if board_event is not None:
                events.append(board_event)

            if ctx.uistate.textfield_open:
                textfield_id = widget_id("textfield")
                ctx.uistate.textfield_str, res = text_field(
                    ctx,
                    id=textfield_id,
                    width=edit_width,
                )
                events.append(res)

        if ctx.uistate.hover_open:
            hover_event = hover(ctx, width=edit_width)
            if hover_event:
                events.append(hover_event)

        for event in events:
            match event:
                case "Add Task":
                    app.open_textfield(
                        ctx, event_type="Add Task", textfield_id=textfield_id
                    )
                case ("Edit Task", {"prefill": text}):
                    app.open_textfield(
                        ctx,
                        event_type="Edit Task",
                        textfield_id=textfield_id,
                        initial_text=text,
                    )
                case "Add Stage":
                    app.open_textfield(
                        ctx, event_type="Add Stage", textfield_id=textfield_id
                    )
                case ("Edit Stage", {"prefill": text}):
                    app.open_textfield(
                        ctx,
                        event_type="Edit Stage",
                        textfield_id=textfield_id,
                        initial_text=text,
                    )
                case "Continue":
                    pass
                case "Accepted":
                    app.handle_accept_textfield(ctx)
                case "Cancelled":
                    app.handle_cancel_textfield(ctx)
                case ("Update Board", {"new_board": new_board}):
                    app.board = new_board
                case ("Show Hover", {"position": point, "text": text}):
                    ctx.uistate.cursor_position = point
                    ctx.uistate.hover_open = True
                    ctx.uistate.hover_text = text
                case "Hide Hover":
                    ctx.uistate.cursor_position = None
                    ctx.uistate.hover_open = False
                case e:
                    logging.error("Unmatched event: %s", e)
                    assert False, "unreachable"

        stdscr.noutrefresh()
        curses.doupdate()


if __name__ == "__main__":
    curses.wrapper(main)
