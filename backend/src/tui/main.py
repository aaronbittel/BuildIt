from __future__ import annotations

import curses
import logging

from src.tui.board import board_widget
from src.tui.components import text, text_field
from src.tui.data import (
    DATA_PATH,
    Board,
    BoardResult,
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
        self.textfield_open = False
        self.show_popup = False
        self.filename = ""
        self.choose_file = not USE_PREFILLED_DATA
        self.textfield_str = ""

        self._pressed_s = 0

    def open_textfield(
        self,
        ctx: UIContext,
        event_type: EventType,
        textfield_id: Id,
        initial_text: str = "",
    ) -> None:
        self.textfield_open = True
        ctx.event_type = event_type
        ctx.uistate.active_id = textfield_id
        self.textfield_str = initial_text

    def handle_accept_textfield(self, ctx: UIContext) -> None:
        assert ctx.event_type is not None

        if ctx.event_type == "Add Task":
            self.board.stage.add(Task(name=self.textfield_str))
        elif ctx.event_type == "Edit Task":
            self.board.stage.task.name = self.textfield_str
        elif ctx.event_type == "Add Stage":
            self.board.add_stage(Stage(title=self.textfield_str))
        elif ctx.event_type == "Edit Stage":
            self.board.stage.title = self.textfield_str
        elif ctx.event_type == "Saving":
            pass
        else:
            logging.error("unexpected event: %s", ctx.event_type)
            assert False, "unreachable"

        ctx.event_type = None
        self.textfield_str = ""
        self.textfield_open = False
        ctx.uistate.active_id = None

    def handle_cancel_textfield(self, ctx: UIContext) -> None:
        ctx.event_type = None
        self.textfield_str = ""
        self.textfield_open = False
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


def main(stdscr: curses.window) -> None:
    curses.set_escdelay(25)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.curs_set(0)

    if USE_PREFILLED_DATA:
        stages = [
            Stage("Backlog", tasks=[Task("Todo 1"), Task("Todo 2")]),
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

    uistate = UiState()
    app = App(board)
    ctx = UIContext(stdscr, uistate)

    stdscr.refresh()
    stdscr.timeout(int(1 / FPS * 1000))

    rows, cols = stdscr.getmaxyx()

    stage_min_width = 25

    def calc_edit_width(cols: int) -> int:
        return min(cols, max(int(0.75 * cols), 25))

    edit_width = calc_edit_width(cols)
    app.textfield_open = False

    logging.info(f"{rows=} {cols=}")

    board_id = widget_id("board")
    textfield_id = widget_id("textfield")
    logging.info(f"{board_id=}")
    logging.info(f"{textfield_id=}")

    while app.running:
        ctx.uistate.key = stdscr.getch()
        ctx.uistate.key_consumed = False
        events = []

        # if ctx.uistate.active_id == board_id:
        #     logging.info("active_id=board")
        # elif ctx.uistate.active_id == textfield_id:
        #     logging.info("active_id=textfield")
        # else:
        #     logging.info("active_id=None")
        if ctx.uistate.active_id != textfield_id and ctx.uistate.key == ord("q"):
            app.running = False
            ctx.uistate.key_consumed = True
            continue

        if ctx.uistate.key == curses.KEY_RESIZE:
            # logging.info(f"{rows=} {cols=}")
            rows, cols = stdscr.getmaxyx()
            edit_width = calc_edit_width(cols)
            ctx.uistate.key_consumed = True

        stdscr.erase()

        with Layout(stdscr, rows, cols) as layout:
            ctx.layout = layout
            with layout.vertical(rows=1, after_spacing=1, child_min_width=5) as ok:
                if ok:
                    display_title(stdscr, layout=layout, title=app.board.title)

            board_event = board_widget(
                ctx,
                board=app.board,
                id=board_id,
                stage_min_width=stage_min_width,
            )
            if board_event is not None:
                events.append(board_event)

            if app.textfield_open:
                app.textfield_str, res = text_field(
                    ctx,
                    id=textfield_id,
                    textfield_str=app.textfield_str,
                    width=edit_width,
                )
                events.append(res)

        # # TODO: Hide away this mess
        # if app.show_popup:
        #     lines = split_text_into_lines(
        #         text=board.stage.task.name, width=edit_width - 3
        #     )
        #     popup_width = max(map(len, lines)) + 4
        #     selected_rect = board_rects[board.selected]
        #     popup_height = len(lines) + 2
        #     popup_y = selected_rect.y + board.stage.selected + 1 - popup_height
        #     popup_x = selected_rect.x + 1
        #
        #     if popup_x + popup_width > cols:
        #         popup_x += cols - (popup_x + popup_width)
        #     if popup_y < 0:
        #         popup_y = selected_rect.y + board.stage.selected + 1 + 1
        #     rect = Rect(
        #         height=popup_height, width=popup_width, y=popup_y, x=popup_x
        #     )
        #     box(rect, lines, rounded=True)

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
                case e:
                    logging.error("Unmatched event: %s", e)
                    assert False, "unreachable"

        stdscr.noutrefresh()
        curses.doupdate()


if __name__ == "__main__":
    curses.wrapper(main)
