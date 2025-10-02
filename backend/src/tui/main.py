from __future__ import annotations

import curses
from datetime import datetime
import logging
from typing import Literal

from src.tui.components import box, text
from src.tui.data import (
    DATA_PATH,
    Board,
    Stage,
    Task,
    __load_state_imm,
    convert_imm_boards_to_boards,
    dump_state,
)
from src.tui.layout import Layout, Rect
from src.tui.utils import KEY_ESC, split_text_into_lines

# TODO: Manuall switching between vertical and horizontal layout for board
# TODO: saving and loading board to db + menu

logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    filemode="w",
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
Mode = Literal["Add Task", "Edit Task", "Add Stage", "Edit Stage", "Saving"]

USE_PREFILLED_DATA = False


class App:
    def __init__(self) -> None:
        self.buf: list[str] = []
        self._cur_mode: Mode | None = None
        self._last_mode: Mode | None = None
        self.show_popup = False
        self.running = True
        self.filename = ""
        self.choose_file = not USE_PREFILLED_DATA

        self._pressed_s = 0

    def handle_key(self, key: int) -> None:
        logging.debug(f"{key=}")
        if 32 <= key <= 126:
            self.buf.append(chr(key))
        elif key == curses.KEY_BACKSPACE and len(self.buf) > 0:
            self.buf = self.buf[:-1]
        elif key == curses.KEY_RESIZE:
            return
        elif key == ord("\n"):
            # Accept Input
            self._cur_mode = None
        elif key == KEY_ESC:
            # Cancel Input
            self._cur_mode = None
            self.buf = []

    def enable_edit_mode(self, mode: Mode, initial_text: str) -> None:
        assert mode == "Edit Stage" or mode == "Edit Task"
        assert initial_text != ""

        self._cur_mode = mode
        self._last_mode = mode
        self.buf = [c for c in initial_text]

    def enable_add_mode(self, mode: Mode) -> None:
        assert mode in ("Add Stage", "Add Task", "Saving")
        self._cur_mode = mode
        self._last_mode = mode
        self.buf = []

    @property
    def textinput_open(self) -> bool:
        return self._cur_mode is not None

    @property
    def edit_content(self) -> str:
        return "".join(self.buf).strip()

    @property
    def last_mode(self) -> Mode:
        assert self._last_mode is not None
        return self._last_mode

    @property
    def cur_mode(self) -> Mode:
        assert self._cur_mode is not None
        return self._cur_mode


def display_title(layout: Layout, title: str) -> None:
    rect = layout.next_rect(height=1)
    text(
        rect,
        title,
        attr=curses.A_BOLD | curses.A_UNDERLINE,
    )


def board_view(layout: Layout, board: Board) -> list[Rect]:
    rects: list[Rect] = []
    for i, stage in enumerate(board.stages):
        content = list(map(lambda t: t.name, stage.tasks))
        rect = layout.next_rect(height=max(len(content) + 2, 5))
        highlighted = i == board.selected
        box(
            rect=rect,
            title=stage.title,
            lines=content,
            selected=board.stage.selected,
            highlighted=highlighted,
            rounded=False,
        )
        rects.append(rect)
    return rects


if not USE_PREFILLED_DATA:
    DATA_PATH.mkdir(exist_ok=True)


def main(stdscr: curses.window) -> None:
    curses.set_escdelay(25)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.curs_set(0)

    app = App()

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

    stdscr.refresh()

    rows, cols = stdscr.getmaxyx()

    stage_min_width = 25

    def calc_edit_width(cols: int) -> int:
        return min(cols, max(int(0.75 * cols), 25))

    edit_width = calc_edit_width(cols)

    board_is_showing = True

    logging.info(f"{rows=} {cols=}")

    while app.running:
        board_rects: list[Rect] = []
        stdscr.erase()
        stdscr.refresh()

        if app.textinput_open:
            curses.curs_set(1)
        else:
            curses.curs_set(0)

        with Layout(stdscr, rows, cols) as layout:
            with layout.vertical(rows=1, after_spacing=1, child_min_width=5) as ok:
                if ok:
                    display_title(layout=layout, title=board.title)

            if len(board.stages) > 0:
                with layout.horizontal(
                    screen_padding=1,
                    spacing=2,
                    after_spacing=1,
                    child_min_width=stage_min_width,
                    columns=len(board.stages),
                ) as h_ok:
                    if h_ok:
                        board_rects = board_view(layout, board)
                        board_is_showing = True

                if not h_ok:
                    with layout.vertical(
                        screen_padding=1,
                        spacing=0,
                        child_min_width=stage_min_width,
                        rows=len(board.stages),
                    ) as v_ok:
                        if v_ok:
                            board_rects = board_view(layout, board)
                        board_is_showing = v_ok

            if app.textinput_open:
                # FIXME: Space does not get rendered
                with layout.horizontal(
                    columns=1,
                    screen_padding=(cols - edit_width) // 2,
                    child_min_width=10,
                ) as ok:
                    if ok:
                        lines = split_text_into_lines(
                            "".join(app.buf), width=edit_width - 4
                        )
                        rect = layout.next_rect(height=max(1, len(lines)) + 2)
                        box(
                            rect,
                            title=app.cur_mode,
                            lines=lines,
                            selected=-1,
                            highlighted=True,
                            rounded=True,
                            squash=False,
                        )
                        if app.cur_mode == "Saving":
                            app.running = False
                        # if not app.buf:
                        #     stdscr.move(rect.y + 1, rect.x + 2)

            # TODO: Hide away this mess
            if app.show_popup:
                lines = split_text_into_lines(
                    text=board.stage.task.name, width=edit_width - 3
                )
                popup_width = max(map(len, lines)) + 4
                selected_rect = board_rects[board.selected]
                popup_height = len(lines) + 2
                popup_y = selected_rect.y + board.stage.selected + 1 - popup_height
                popup_x = selected_rect.x + 1

                if popup_x + popup_width > cols:
                    popup_x += cols - (popup_x + popup_width)
                if popup_y < 0:
                    popup_y = selected_rect.y + board.stage.selected + 1 + 1
                rect = Rect(
                    height=popup_height, width=popup_width, y=popup_y, x=popup_x
                )
                box(rect, lines, rounded=True)

        key = stdscr.getch()

        if app.textinput_open:
            logging.info(f"Textinput Mode: {app.cur_mode}")
            app.handle_key(key)
            if not app.textinput_open and len(app.edit_content) > 0:
                if app.last_mode == "Add Task":
                    board.stage.add(Task(name=app.edit_content))
                elif app.last_mode == "Edit Task":
                    board.stage.task.name = app.edit_content
                elif app.last_mode == "Add Stage":
                    board.add_stage(Stage(title=app.edit_content))
                elif app.last_mode == "Edit Stage":
                    board.stage.title = app.edit_content
                elif app.last_mode == "Saving":
                    app.filename = (
                        app.edit_content
                        if app.edit_content
                        else datetime.now().strftime(r"%y_%m_%d-%H_%M_%S")
                    )
        else:
            logging.info("Normal Mode")
            if key == ord("q"):
                if not USE_PREFILLED_DATA:
                    app.enable_add_mode(mode="Saving")
                    dump_state(board=board, filename=app.filename)
                else:
                    app.running = False
            elif key == ord("j"):
                board.stage.next_task()
            elif key == ord("k"):
                board.stage.prev_task()
            elif key == ord("n"):
                board.forward_task()
            elif key == ord("p"):
                board.recall_task()
            elif key == ord("a"):
                app.enable_add_mode(mode="Add Task")
            elif key == ord("e"):
                if len(board.stage) > 0:
                    app.enable_edit_mode(
                        mode="Edit Task", initial_text=board.stage.task.name
                    )
                else:
                    app.enable_add_mode(mode="Add Task")
            elif key == ord("x"):
                if len(board.stage) > 0:
                    board.stage.pop()
            elif key == ord("s"):
                if len(board.stage) == 0 or not board_is_showing:
                    continue
                rect = board_rects[board.selected]
                if rect.width - 4 < len(board.stage.task.name):
                    app.show_popup = True
                    app._pressed_s += 1
            elif key == ord("J"):
                board.stage.move_task(1)
            elif key == ord("K"):
                board.stage.move_task(-1)
            elif key == ord("A"):
                app.enable_add_mode(mode="Add Stage")
            elif key == ord("E"):
                app.enable_edit_mode(mode="Edit Stage", initial_text=board.stage.title)
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

            # FIXME: make it better
            if key != ord("s") and app.show_popup:
                app._pressed_s += 1
                app.show_popup = False
            elif key == ord("s") and app._pressed_s % 2 == 0:
                app.show_popup = False

        if key == curses.KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            edit_width = calc_edit_width(cols)
            logging.info(f"{rows=} {cols=}")


if __name__ == "__main__":
    curses.wrapper(main)
