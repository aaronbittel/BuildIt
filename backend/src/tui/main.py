import curses
from curses.textpad import rectangle
import logging
from typing import Literal

from data import Board, Stage, Task

from src.tui.components import box, text
from src.tui.layout import Layout
from src.tui.utils import KEY_ESC, show_cursor, split_text_into_lines

logging.basicConfig(filename="app.log", level=logging.DEBUG, filemode="w")
Mode = Literal["Add Task", "Edit Task", "Add Stage", "Edit Stage"]


class App:
    def __init__(self) -> None:
        self.buf: list[str] = []
        self._cur_mode: Mode | None = None
        self._last_mode: Mode | None = None

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
        assert mode == "Add Stage" or mode == "Add Task"
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


def board_view(layout: Layout, board: Board) -> None:
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


def main(stdscr: curses.window) -> None:
    curses.set_escdelay(25)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.curs_set(0)

    stages = [
        Stage("Backlog", tasks=[Task("Todo 1"), Task("Todo 2")]),
        Stage("In Progress", tasks=[Task("Task 1"), Task("Task 2"), Task("Task 3")]),
        Stage("Done", tasks=[Task("Done 1"), Task("Done 2"), Task("Done 3")]),
    ]
    board = Board(title="Main Board", stages=stages)

    stdscr.refresh()

    rows, cols = stdscr.getmaxyx()

    stage_min_width = 25

    def calc_edit_width() -> int:
        return max(int(0.75 * cols), 25)

    edit_width = calc_edit_width()

    app = App()

    logging.info(f"{rows=} {cols=}")

    while True:
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

            with layout.horizontal(
                screen_padding=1,
                spacing=2,
                after_spacing=1,
                child_min_width=stage_min_width,
                columns=len(board.stages),
            ) as h_ok:
                if h_ok:
                    board_view(layout, board)

            if not h_ok:
                with layout.vertical(
                    spacing=0,
                    child_min_width=stage_min_width,
                    rows=len(board.stages),
                ) as v_ok:
                    if v_ok:
                        board_view(layout, board)

            if app.textinput_open:
                # FIXME: Space does not get rendered
                lines = split_text_into_lines("".join(app.buf), width=edit_width - 3)
                with layout.horizontal(
                    columns=1,
                    screen_padding=(cols - edit_width) // 2,
                    child_min_width=edit_width,
                ) as ok:
                    if ok:
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
                        if not app.buf:
                            stdscr.move(rect.y + 1, rect.x + 2)

        key = stdscr.getch()

        if app.textinput_open:
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
        else:
            if key == ord("q"):
                break
            elif key == ord("j"):
                board.stage.next_task()
            elif key == ord("k"):
                board.stage.prev_task()
            elif key == ord("n"):
                board.forward_task()
            elif key == ord("p"):
                board.recall_task()
            elif key == ord("J"):
                board.stage.move_task(1)
            elif key == ord("K"):
                board.stage.move_task(-1)
            elif key == ord("a"):
                app.enable_add_mode(mode="Add Task")
            elif key == ord("e"):
                app.enable_edit_mode(
                    mode="Edit Task", initial_text=board.stage.task.name
                )
            elif key == ord("A"):
                app.enable_add_mode(mode="Add Stage")
            elif key == ord("E"):
                app.enable_edit_mode(mode="Edit Stage", initial_text=board.stage.title)
            elif key == ord("\t"):
                board.next()
            elif key == curses.KEY_BTAB:
                board.prev()
            elif key == ord("\n"):
                board = board.goto_next_board(
                    stage_idx=board.selected, task_idx=board.stage.selected
                )
            elif key == KEY_ESC:
                board = board.goto_prev_board()

        if key == curses.KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            edit_width = calc_edit_width()
            logging.info(f"{rows=} {cols=}")


if __name__ == "__main__":
    curses.wrapper(main)
