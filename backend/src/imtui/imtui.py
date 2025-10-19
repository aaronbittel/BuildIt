from __future__ import annotations

from contextlib import contextmanager, suppress
from copy import deepcopy
import curses
import _curses
from enum import Enum, auto
import logging
from dataclasses import dataclass, field
from typing import NamedTuple

from src.tui.board import Board, Stage, Task
from src.tui.event import SwitchBoard
from src.tui.ui import Id, widget_id
from src.tui.utils import (
    ELLIPSIS,
    KEY_ESC,
    clamp_width,
    clear_rect,
    split_text_into_lines,
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

# "" "" "" "" "" ""
#  

FPS = 30


@dataclass(frozen=True)
class Vec2:
    y: int = 0
    x: int = 0


UNSET = Vec2(-1, -1)


@dataclass
class Hover:
    open: bool = False
    pos: Vec2 = field(default_factory=lambda: Vec2())


@dataclass
class Textfield:
    open: bool = False
    content: str = ""


@dataclass
class FilterTextfield(Textfield):
    active: bool = False


class Mode(Enum):
    AddTask = auto()
    EditTask = auto()
    AddStage = auto()
    EditStage = auto()


@dataclass
class App:
    board: Board

    mode: Mode | None = field(default=None, init=False)
    shutdown: bool = field(default=False, init=False)
    line: int = field(default=0, init=False)

    hover: Hover = field(default_factory=lambda: Hover(), init=False)

    input_textfield: Textfield = field(default_factory=lambda: Textfield(), init=False)

    filter_textfield: FilterTextfield = field(
        default_factory=lambda: FilterTextfield(), init=False
    )


@dataclass
class TUI:
    stdscr: curses.window
    rows: int
    cols: int

    active_id: Id = -1
    # TODO: How does negative focus request work?
    focus_request_offset: int | None = field(default=None, init=False)
    focus_request_id: Id | None = None
    last_item_id: Id | None = None
    tab_counter: int | None = None

    key: int = field(default=-1, init=False)

    sameline_active: bool = field(default=False, init=False)
    spacing_w: int = field(default=0, init=False)
    prev_pos: Vec2 = field(default_factory=lambda: UNSET, init=False)
    prev_size: Vec2 = field(default_factory=lambda: UNSET, init=False)
    prev_max_height: int = field(default=0, init=False)

    cursor_pos: Vec2 = field(default_factory=lambda: Vec2(0, 0))
    temp_cursor_pos: Vec2 | None = field(default=None, init=False)

    def set_keyboard_focus_here(self, offset: int = 0) -> None:
        assert offset == 0, "offset -1 or 1 currently not implemented"
        assert offset in (-1, 0, 1), "offset not in (-1, 0, 1) are forbidden"
        self.focus_request_offset = offset

    def request_focus(self, id: Id) -> None:
        self.focus_request_id = id

    def resolve_focus_request(self) -> None:
        if self.focus_request_id is not None:
            self.active_id = self.focus_request_id
            self.focus_request_id = None

    def temp_pos(self, y: int, x: int) -> None:
        self.temp_cursor_pos = Vec2(y=y, x=x)

    def update_next_widget_position(self, height: int, width: int) -> None:
        if self.temp_cursor_pos is not None:
            self.temp_cursor_pos = None
            return

        self.prev_max_height = max(self.prev_max_height, height)
        self.prev_pos = self.cursor_pos
        # TODO: dont use vec2 here?
        self.prev_size = Vec2(y=height, x=width)
        self.cursor_pos = Vec2(y=self.cursor_pos.y + self.prev_max_height, x=0)

    def sameline(self, spacing: int = 0) -> None:
        self.sameline_active = True
        self.spacing_w = spacing
        self.prev_max_height = max(self.prev_size.y, self.prev_max_height)

    def __begin(self) -> None:
        self.cursor_pos = Vec2(0, 0)

    def __end(self) -> None:
        pass

    @contextmanager
    def begin(self) -> None:
        try:
            self.__begin()
            yield
        finally:
            self.__end()

    @property
    def next_widget_pos(self) -> Vec2:
        if self.temp_cursor_pos is not None:
            return self.temp_cursor_pos

        if self.sameline_active:
            self.sameline_active = False
            self.cursor_pos = Vec2(
                y=self.prev_pos.y,
                x=self.prev_pos.x + self.prev_size.x + self.spacing_w,
            )
            return self.cursor_pos
        self.prev_max_height = 0
        return self.cursor_pos


class Rect(NamedTuple):
    height: int
    width: int
    y: int
    x: int


def stage_view(
    tui: TUI,
    stage: Stage,
    width: int | None = None,
    padding: int = 1,
    filter_str: str | None = None,
    *,
    highlighted: bool = False,
) -> Rect:
    lines = [
        task.name
        for task in stage
        if not filter_str or task.name.lower().startswith(filter_str)
    ]
    height = max(len(lines) + 2, 5)
    return mybox(
        tui=tui,
        title=stage.title,
        lines=lines,
        height=height,
        width=width,
        padding=padding,
        selected=stage.selected,
        rounded=False,
        highlighted=highlighted,
    )


def mybox(
    tui: TUI,
    title: str = "",
    lines: list[str] | None = None,
    padding: int = 1,
    selected: int | None = None,
    *,
    height: int | None = None,
    width: int | None = None,
    y: int | None = None,
    x: int | None = None,
    highlighted: bool = False,
    rounded: bool = False,
    cursor: bool = False,
    clear_background: bool = False,
) -> Rect:
    lines = lines if lines is not None else []
    height = height if height is not None else len(lines) + 2
    box_width = (
        lambda: max(len(title), max((len(line) for line in lines), default=2))
        + 2
        + 2 * padding
    )
    box_width = width if width is not None else box_width()
    content_width = box_width - 2 - 2 * padding  # border(2)

    if y is not None and x is not None:
        tui.temp_pos(y=y, x=x)
    pos = tui.next_widget_pos
    tui.update_next_widget_position(height, box_width)

    if clear_background:
        clear_rect(
            tui.stdscr, rect=Rect(height=height, width=box_width, y=pos.y, x=pos.x)
        )

    draw_border(
        tui.stdscr,
        # NOTE: Do I need the Rect type at all?
        rect=Rect(height=height, width=box_width, y=pos.y, x=pos.x),
        title=title,
        rounded=True,
        border_colorpair=1 if highlighted else 0,
    )

    for row, line in enumerate(lines):
        if len(line) > content_width:
            line = line[: content_width - 1] + ELLIPSIS
        tui.stdscr.addstr(pos.y + row + 1, pos.x + 1 + padding, line)

    if highlighted and selected is not None:
        tui.stdscr.chgat(
            pos.y + 1 + selected,
            pos.x + 1,
            box_width - 2,
            curses.color_pair(1) | curses.A_REVERSE,
        )

    if cursor:
        x_offset = len(lines[-1]) if lines else 0
        y_offset = max(1, len(lines))
        tui.stdscr.chgat(
            pos.y + y_offset,
            pos.x + 1 + padding + x_offset,
            1,
            curses.A_REVERSE,
        )

    return Rect(height=height, width=box_width, y=pos.y, x=pos.x)


def draw_border(
    stdscr: curses.window,
    rect: Rect,
    title: str = "",
    border_colorpair: int = 0,
    *,
    rounded: bool = False,
):
    upper_left_corner = "╭" if rounded else "┌"
    upper_right_corner = "╮" if rounded else "┐"
    lower_left_corner = "╰" if rounded else "└"
    lower_right_corner = "╯" if rounded else "┘"

    height, width, y, x = rect

    color = curses.color_pair(border_colorpair)

    stdscr.addch(y, x, upper_left_corner, color)
    stdscr.addstr(y, x + 1, "─" * (width - 2), color)
    # FIXME:I should not need `suppress()` here
    with suppress(_curses.error):
        stdscr.addch(y, x + width - 1, upper_right_corner, color)

    if title:
        if len(title) > width:
            title = title[: width - 1] + ELLIPSIS
        stdscr.addstr(y, x + (width - len(title)) // 2, title, curses.A_BOLD)

    for row in range(1, height - 1):
        with suppress(_curses.error):
            stdscr.addch(y + row, x, "│", color)
            stdscr.addch(y + row, x + width - 1, "│", color)

    stdscr.addch(y + height - 1, x, lower_left_corner, color)
    stdscr.addstr(y + height - 1, x + 1, "─" * (width - 2), color)
    with suppress(_curses.error):
        stdscr.addch(y + height - 1, x + width - 1, lower_right_corner, color)


def text(
    tui: TUI,
    msg: str,
    attr: int | None = None,
    y: int | None = None,
    x: int | None = None,
) -> None:
    if y is not None and x is not None:
        tui.temp_pos(y=y, x=x)

    attr = attr if attr is not None else curses.A_NORMAL

    pos = tui.next_widget_pos
    height, width = 1, len(msg)
    tui.update_next_widget_position(height, width)

    tui.stdscr.addstr(pos.y, pos.x, msg, attr)


def textfield(
    tui: TUI,
    id: Id,
    content: str,
    width: int,
    title: str = "",
    height: int | None = None,
    *,
    highlighted: bool = False,
    enter_accept: bool = False,
    escape_cancel: bool = False,
) -> tuple[str, bool]:
    if tui.focus_request_offset == 0:
        tui.active_id = id
        tui.focus_request_offset -= 1

    edit_width = width - 4
    lines, _ = split_text_into_lines(text=content, width=edit_width)
    height = height if height is not None else max(1, len(lines)) + 2
    mybox(
        tui,
        title=title,
        lines=lines,
        width=width,
        height=height,
        highlighted=highlighted,
        cursor=True,
    )

    changed = False

    if tui.active_id != id:
        return content, changed

    if 32 <= tui.key <= 126:
        content += chr(tui.key)
        if not enter_accept:
            changed = True
    elif tui.key == curses.KEY_BACKSPACE:
        if len(content) > 0:
            content = content[:-1]
            if not enter_accept:
                changed = True
    elif tui.key == ord("\n") and enter_accept:
        if enter_accept:
            changed = True
    elif tui.key == KEY_ESC and escape_cancel:
        content = ""

    return content.strip(), changed


MIN_STAGE_WIDTH = 25


def main(stdscr: curses.window) -> None:
    curses.set_escdelay(25)
    curses.start_color()
    assert curses.can_change_color(), "Terminal cannot redefine colors"
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_BLUE)

    curses.curs_set(0)

    rows, cols = stdscr.getmaxyx()

    stdscr.refresh()
    stdscr.timeout(int(1 / FPS * 1000))

    logging.info(f"{rows=} {cols=}")

    STAGE_SPACING = 2
    SCREEN_PADDING = 0

    board_id = widget_id("board")

    tui = TUI(stdscr, rows, cols, active_id=board_id)
    app = App(
        board=Board(
            title="Main Board Title",
            stages=[
                Stage(
                    title="Backlog",
                    tasks=[Task(name) for name in ("ABC", "CDF", "ABC2")],
                ),
                Stage(
                    title="In Progress",
                    tasks=[Task(name) for name in ("ABC", "CDF", "ABC2", "CDF2")],
                ),
                Stage(
                    title="Done",
                    tasks=[Task(name) for name in ("LDSJ", "ABC3", "CDF2")],
                ),
            ],
        )
    )
    # app = App(board=Board.default(title="Main Board Title", prefilled=True))

    while True:
        tui.resolve_focus_request()

        tui.key = stdscr.getch()
        if not app.shutdown and tui.key == ord("q") and not app.input_textfield.open:
            app.shutdown = True
        elif tui.key == curses.KEY_RESIZE:
            tui.rows, tui.cols = stdscr.getmaxyx()

        if not app.shutdown and tui.active_id == board_id:
            board_handle_key(tui=tui, app=app, key=tui.key)

        stdscr.erase()

        board = app.board

        stage_rects: list[Rect] = []

        content_width = tui.cols - (len(board) - 1) * STAGE_SPACING - 2 * SCREEN_PADDING
        width_per_stage = content_width // len(board)
        use_horizontal_layout = lambda: width_per_stage >= MIN_STAGE_WIDTH

        with tui.begin():
            tui.cursor_pos = Vec2(
                y=tui.cursor_pos.y, x=(tui.cols - len(board.title)) // 2
            )
            text(tui, msg=board.title)
            tui.cursor_pos = Vec2(y=tui.cursor_pos.y + 1, x=tui.cursor_pos.x)

            for i, stage in enumerate(board.stages):
                highlighted = (
                    tui.active_id == board_id or app.input_textfield.open
                ) and board.selected == i
                if use_horizontal_layout():
                    if i > 0:
                        tui.sameline(spacing=STAGE_SPACING)
                    width = width_per_stage
                else:
                    width = tui.cols
                filter_str = (
                    app.filter_textfield.content.lower()
                    if app.filter_textfield.active
                    else None
                )
                stage_rects.append(
                    stage_view(
                        tui,
                        stage=stage,
                        width=width,
                        highlighted=highlighted,
                        filter_str=filter_str,
                    )
                )

            stage_view(tui, stage=board.stages[0], width=width)

            if app.input_textfield.open:
                edit_width = clamp_width(tui.cols, perc=0.75, min_width=25)
                screen_padding = (tui.cols - edit_width) // 2
                tui.cursor_pos = Vec2(y=tui.cursor_pos.y, x=screen_padding)

                tui.set_keyboard_focus_here()
                app.input_textfield.content, accepted = textfield(
                    tui,
                    id=widget_id("textfield"),
                    content=app.input_textfield.content,
                    title="Textfield",
                    width=edit_width,
                    highlighted=True,
                    enter_accept=True,
                )

                if accepted:
                    msg = app.input_textfield.content
                    app.input_textfield = Textfield()
                    tui.active_id = board_id
                    if msg != "":
                        match app.mode:
                            case Mode.AddTask:
                                board.stage.add(Task(name=msg))
                            case Mode.EditTask:
                                board.stage.task.name = msg
                            case Mode.AddStage:
                                board.add_stage(Stage(title=msg))
                            case Mode.EditTask:
                                board.stage.title = msg
                if tui.key == KEY_ESC:
                    app.input_textfield = Textfield()
                    tui.active_id = board_id

            if app.filter_textfield.open:
                filter_width = clamp_width(tui.cols, perc=0.5, min_width=15)
                screen_padding = (tui.cols - filter_width) // 2
                tui.cursor_pos = Vec2(y=tui.cursor_pos.y, x=screen_padding)

                tui.set_keyboard_focus_here()
                app.filter_textfield.content, changed = textfield(
                    tui,
                    id=widget_id("filter-textfield"),
                    content=app.filter_textfield.content,
                    title="Filter",
                    width=filter_width,
                    highlighted=True,
                )

                if tui.key == KEY_ESC or tui.key == ord("\n"):
                    app.filter_textfield.active = app.filter_textfield.content != ""
                    app.filter_textfield.open = False
                    tui.active_id = board_id

            if app.hover.open:
                task = board.stage[board.stage.selected]
                stage_rect = stage_rects[board.selected]

                hover_width = clamp_width(tui.cols, perc=0.65, min_width=10)
                lines, _ = split_text_into_lines(text=task.name, width=hover_width)
                width = max(len(line) for line in lines) + 4

                y = stage_rect.y + 1 + board.stage.selected - len(lines) - 2
                if y < 0:
                    y = stage_rect.y + 1 + board.stage.selected + 1
                x = stage_rect.x + 1
                if x + width > tui.cols:
                    x = stage_rect.x + stage_rect.width - width

                mybox(tui, lines=lines, width=width, y=y, x=x, clear_background=True)

            if app.filter_textfield.active:
                filter_str = f"filter: {app.filter_textfield.content}"
                filter_x = tui.cols - len(filter_str) - 1
                text(
                    tui,
                    msg="",
                    y=0,
                    x=filter_x - 1,
                    attr=curses.color_pair(2) | curses.A_REVERSE,
                )
                text(
                    tui,
                    msg="",
                    y=0,
                    x=tui.cols - 1,
                    attr=curses.color_pair(2) | curses.A_REVERSE,
                )
                text(tui, filter_str, y=0, x=filter_x, attr=curses.color_pair(2))

            status_msg = f"Currently selected: {board.stage.task.name}"
            status_y = tui.rows - 1
            status_x = (tui.cols - len(status_msg)) // 2
            text(tui, msg="▎", y=status_y, x=status_x - 1, attr=curses.A_REVERSE)
            text(
                tui,
                msg=status_msg,
                y=status_y,
                x=status_x,
                attr=curses.A_REVERSE,
            )
            text(
                tui,
                msg="▐",
                y=status_y,
                x=status_x + len(status_msg),
                attr=curses.A_REVERSE,
            )

        if app.shutdown:
            if app.line >= tui.rows:
                break
            for row in range(app.line):
                text(tui, msg=" " * tui.cols, y=row, x=0)
            app.line += 1

        stdscr.noutrefresh()
        curses.doupdate()


def board_handle_key(tui: TUI, app: App, key: int) -> None:
    if key == -1:
        return

    board = app.board

    if key == ord("s"):
        app.hover.open = not app.hover.open
    else:
        app.hover.open = False

        if key == ord("\t"):
            board.selected = (board.selected + 1) % len(board)
        elif key == curses.KEY_BTAB:
            board.selected = (board.selected - 1) % len(board)
        elif key == ord("j"):
            board.stage.next_task()
        elif key == ord("k"):
            board.stage.prev_task()
        elif key == ord("a"):
            app.input_textfield = Textfield(open=True)
            app.mode = Mode.AddTask
        elif key == ord("e"):
            app.input_textfield = Textfield(open=True, content=board.stage.task.name)
            app.mode = Mode.EditTask
        elif key == ord("n"):
            board.forward_task()
        elif key == ord("p"):
            board.recall_task()
        elif key == ord("x"):
            if len(board.stage) > 0:
                board.stage.pop()
        elif key == ord("f"):
            app.filter_textfield = FilterTextfield(
                open=True, active=True, content=app.filter_textfield.content
            )
        elif key == ord("F"):
            app.filter_textfield = FilterTextfield()
        elif key == ord("J"):
            board.stage.move_task(1)
        elif key == ord("K"):
            board.stage.move_task(-1)
        elif key == ord("A"):
            app.input_textfield = Textfield(open=True)
            app.mode = Mode.AddStage
        elif key == ord("E"):
            app.input_textfield = Textfield(open=True, content=board.stage.title)
            app.mode = Mode.EditStage
        elif key == ord("\n"):
            if len(board.stage) > 0:
                board = board.goto_next_board(prefilled=True)
                app.filter_textfield = FilterTextfield()
        elif key == KEY_ESC:
            if board.prev_board is not None:
                board = board.goto_prev_board()
                app.filter_textfield = FilterTextfield()

    # consume key
    tui.key = -1

    app.board = board


if __name__ == "__main__":
    curses.wrapper(main)
