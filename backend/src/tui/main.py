from contextlib import contextmanager, suppress
import curses
from curses import textpad
import _curses
from collections import namedtuple
from functools import wraps

_DEBUG_BUFFER: list[str] | None = None
_DEBUG_WINDOW: curses.window | None = None

ROUNDED_TOPLEFT = "╭"
ROUNDED_TOPRIGHT = "╮"
ROUNDED_BOTTOMRIGHT = "╯"
ROUNDED_BOTTOMLEFT = "╰"
VERTICAL_BAR = "│"
HORIZONTAL_BAR = "─"
ELLIPSIS = "…"

KEY_IGNORE = 0
KEY_EXIT = 7

PREF_EDIT_WIDTH = 48

# TODO: use floats for calculation for precise results
# TODO: use win.mvwin and / or win.resize instead of creating new windows (if its
# easier)
# TODO: Look into this: erase, noutrefresh, doupdate, etc.


def hide_cursor(func):
    @wraps(func)
    def wrapper_func(win: curses.window, *args, **kwargs):
        curses.curs_set(0)
        try:
            return func(win, *args, **kwargs)
        finally:
            curses.curs_set(1)

    return wrapper_func


Stage = namedtuple("Stage", ["name", "tasks"])

stages = [
    Stage(name="Backlog", tasks=["Todo 1", "Todo 2", "Todo 3"]),
    Stage(name="In Progress", tasks=["Task 1", "Task 2", "Long Long Long Message"]),
    Stage(name="Done", tasks=["Finished 1", "Finished 2", "Finished 3", "Another One"]),
]


class StageView:
    def __init__(
        self,
        stage: Stage,
        min_height: int = 4,
        width: int = 20,
        highlighted: bool = False,
    ) -> None:
        self.stage = stage
        self.min_height = min_height
        self.y = 0
        self.x = 0

        self.content_height = max(len(stage.tasks), min_height)
        self.view_height = self.content_height + 2

        self._win: curses.window | None = None
        self.highlighted = highlighted
        self.selected = 0

    def _calculate_heights(self) -> None:
        self.content_height = max(len(self.stage.tasks), self.min_height)
        self.view_height = self.content_height + 2

    def resize(self, y: int, x: int, width: int) -> None:
        self.y = y
        self.x = x
        self.width = width

        self._calculate_heights()

        self.clear()

        try:
            self._win = curses.newwin(self.view_height, width, y, x)
        except _curses.error:
            self._win = None

    def draw(self) -> None:
        if not self._can_draw():
            return

        self._win.clear()
        self._draw_border()

        title = self.stage.name
        if len(title) > self.width:
            title = title[: self.width - 1] + ELLIPSIS

        if self.width > 4:
            self._win.addstr(0, (self.width - len(title)) // 2, title)
            for i, task in enumerate(self.stage.tasks):
                text = task
                if len(text) > self.width - 5:
                    text = text[: self.width - 5] + ELLIPSIS
                with suppress(_curses.error):
                    self._win.addstr(i + 1, 2, text)
                if self.highlighted:
                    if i == self.selected:
                        self._win.chgat(i + 1, 1, self.width - 2, curses.color_pair(2))

        self._win.refresh()

    def clear(self) -> None:
        if not self._can_draw():
            return

        self._win.clear()
        self._win.refresh()

    def _can_draw(self) -> bool:
        if self._win is None:
            return False

        height, width = self._win.getmaxyx()
        return height >= 4 and width >= 4

    def _draw_border(self) -> None:
        if not self._can_draw():
            return

        color = curses.color_pair(1) if self.highlighted else curses.color_pair(0)
        self._win.addch(0, 0, curses.ACS_ULCORNER, color)
        self._win.hline(0, 1, curses.ACS_HLINE, self.width - 2, color)
        self._win.addch(0, self.width - 1, curses.ACS_URCORNER, color)

        for y in range(1, self.content_height + 1):
            self._win.addch(y, 0, curses.ACS_VLINE, color)
            with suppress(_curses.error):
                self._win.addch(y, self.width - 1, curses.ACS_VLINE, color)

        self._win.addch(self.view_height - 1, 0, curses.ACS_LLCORNER, color)
        self._win.hline(
            self.view_height - 1, 1, curses.ACS_HLINE, self.width - 2, color
        )
        with suppress(_curses.error):
            self._win.addch(
                self.view_height - 1, self.width - 1, curses.ACS_LRCORNER, color
            )

    def add(self, task: str) -> None:
        self.stage.tasks.append(task)
        if len(self.stage.tasks) > self.content_height:
            self._calculate_heights()
            self._win = curses.newwin(self.view_height, self.width, self.y, self.x)

    def next(self) -> None:
        self.selected = min(self.selected + 1, len(self.stage.tasks) - 1)

    def prev(self) -> None:
        self.selected = max(self.selected - 1, 0)

    def update(self, task: str) -> None:
        self.stage.tasks[self.selected] = task

    @property
    def text(self) -> str:
        return self.stage.tasks[self.selected]

    @property
    def bottom(self) -> int:
        return self.y + self.view_height


def border(win: curses.window, title: str | None = None) -> curses.window:
    org_height, org_width = win.getmaxyx()
    org_y, org_x = win.getbegyx()

    height, width = org_height + 2, org_width + 2
    border_win = curses.newwin(height, width, org_y - 1, org_x - 1)

    border_win.addstr(
        0, 0, ROUNDED_TOPLEFT + HORIZONTAL_BAR * (width - 2) + ROUNDED_TOPRIGHT
    )

    for i in range(height - 2):
        border_win.addstr(i + 1, 0, VERTICAL_BAR)
        border_win.addstr(i + 1, width - 1, VERTICAL_BAR)
    border_win.addstr(height - 1, 0, ROUNDED_BOTTOMLEFT)
    border_win.addstr(height - 1, 1, HORIZONTAL_BAR * (width - 2))

    with suppress(_curses.error):
        border_win.addstr(
            height - 1,
            0,
            ROUNDED_BOTTOMLEFT + HORIZONTAL_BAR * (width - 2) + ROUNDED_BOTTOMRIGHT,
        )

    if title:
        border_win.addstr(0, 2, title)
    border_win.refresh()
    return border_win


def get_input(
    y: int, x: int, width: int, height: int = 1, text: str | None = None
) -> str:
    def validator(ch: int) -> int:
        if ch == ord("\n") or ch == curses.KEY_RESIZE:
            return KEY_EXIT
        return ch

    if text is not None and width < len(text):
        return ""

    edit_win = curses.newwin(height, width, y, x)
    if text is not None:
        edit_win.addstr(0, 0, text)
    border_win = border(edit_win, title="Add" if text is None else "Edit")
    textbox = textpad.Textbox(edit_win, insert_mode=True)

    with show_cursor():
        text = textbox.edit(validator).strip()

    border_win.clear()
    edit_win.clear()
    border_win.refresh()
    edit_win.refresh()
    return text


class StageViewList:
    def __init__(
        self,
        y: int,
        stages: list[Stage],
        space_perc: float,
        cols: int,
        min_width=20,
    ) -> None:
        assert len(stages) > 0

        self.y = y
        self.stages = stages
        self.cols = cols
        self.space_perc = space_perc
        self.min_width = min_width

        self.use_vertical_layout = False

        self.stage_views = [StageView(stage) for stage in stages]

        self._selected = 0
        self.selected.highlighted = True
        self._dirty_views: set[StageView] = set(self.stage_views)

        self.resize(cols)

    def draw(self) -> None:
        for stage in self._dirty_views:
            stage.draw()
        self._dirty_views.clear()

    def resize(self, cols: int) -> None:
        self.cols = cols

        space_len = int(self.cols * self.space_perc)
        content_width = self.cols - space_len * (len(self.stages) + 1)
        width_per_stageview = content_width // len(self.stages)

        self.use_vertical_layout = width_per_stageview < self.min_width

        for view in self.stage_views:
            view.clear()

        if self.use_vertical_layout:
            self._vertical_layout(cols)
        else:
            self._horizontal_layout(space_len, width_per_stageview)

        self._dirty_views = set(self.stage_views)

    def _vertical_layout(self, cols: int) -> None:
        y = self.y
        for view in self.stage_views:
            view.resize(y=y, x=0, width=cols)
            y += view.view_height

    def _horizontal_layout(self, space_len: int, width_per_stageview: int) -> None:
        for i, view in enumerate(self.stage_views):
            x = space_len + i * (width_per_stageview + space_len)
            view.resize(y=self.y, x=x, width=width_per_stageview)

    def selected_task(self) -> str:
        return self.selected.text

    def update_task(self, task: str) -> str:
        self._dirty_views.add(self.selected)
        return self.selected.update(task)

    def add(self, task: str) -> None:
        self._dirty_views.add(self.selected)
        self.selected.add(task)
        self.resize(self.cols)

    def next_task(self) -> None:
        self._dirty_views.add(self.selected)
        self.selected.next()
        self._dirty_views.add(self.selected)

    def prev_task(self) -> None:
        self._dirty_views.add(self.selected)
        self.selected.prev()
        self._dirty_views.add(self.selected)

    def next_stage(self) -> None:
        self._dirty_views.add(self.selected)
        self.selected.highlighted = False
        self._selected += 1
        if self._selected >= len(self.stage_views):
            self._selected = 0
        self.selected.highlighted = True
        self._dirty_views.add(self.selected)

    @property
    def selected(self) -> StageView:
        return self.stage_views[self._selected]

    @property
    def bottom(self) -> int:
        if self.use_vertical_layout:
            return self.stage_views[-1].bottom
        return self.y + max(map(lambda view: view.view_height, self.stage_views))


@contextmanager
def show_cursor():
    try:
        curses.curs_set(1)
        yield
    finally:
        curses.curs_set(0)


@contextmanager
def debug_block():
    global _DEBUG_BUFFER
    global _DEBUG_WINDOW

    _DEBUG_BUFFER = []
    if _DEBUG_WINDOW is not None:
        _DEBUG_WINDOW.clear()
        _DEBUG_WINDOW.refresh()

    try:
        yield
    finally:
        _DEBUG_WINDOW = curses.newwin(
            len(_DEBUG_BUFFER), curses.COLS, curses.LINES - len(_DEBUG_BUFFER), 0
        )
        for i, text in enumerate(_DEBUG_BUFFER):
            _DEBUG_WINDOW.addstr(i, 0, text)
        _DEBUG_WINDOW.refresh()
        _DEBUG_BUFFER = None


def debug(msg: str) -> None:
    global _DEBUG_BUFFER
    if _DEBUG_BUFFER is None:
        win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        win.addstr(msg)
        win.refresh()
        return
    _DEBUG_BUFFER.append(msg)


def title(win: curses.window, cols: int, text: str) -> None:
    win.move(0, 0)
    win.clrtoeol()
    win.refresh()

    if cols < len(text):
        return
    win.addstr(0, cols // 2 - len(text) // 2, text, curses.A_BOLD | curses.A_UNDERLINE)


@hide_cursor
def main(stdscr: curses.window):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)

    stdscr.keypad(True)

    stdscr.clear()
    stdscr.refresh()

    title_text = "Buildit! - Tui"
    title(stdscr, cols=curses.COLS, text=title_text)

    stage_view_list = StageViewList(
        y=2, stages=stages, space_perc=0.03, cols=curses.COLS
    )

    edit_width = PREF_EDIT_WIDTH if curses.COLS > PREF_EDIT_WIDTH else curses.COLS - 2

    running = True

    while running:
        stage_view_list.draw()

        key = stdscr.getch()
        if key == ord("q"):
            running = False
        elif key == ord("a"):
            _, cols = stdscr.getmaxyx()
            got = get_input(
                y=stage_view_list.bottom + 1,
                x=cols // 2 - edit_width // 2,
                width=edit_width,
            )
            if got != "":
                stage_view_list.add(got)
        elif key == ord("e"):
            _, cols = stdscr.getmaxyx()
            got = get_input(
                y=stage_view_list.bottom + 1,
                x=cols // 2 - edit_width // 2,
                width=edit_width,
                text=stage_view_list.selected_task(),
            )
            if got != "":
                stage_view_list.update_task(got)
        elif key == ord("j"):
            stage_view_list.next_task()
        elif key == ord("k"):
            stage_view_list.prev_task()
        elif key == ord("\t"):
            stage_view_list.next_stage()
        elif key == curses.KEY_RESIZE:
            _, cols = stdscr.getmaxyx()
            title(stdscr, cols=cols, text=title_text)
            stage_view_list.resize(cols)
            edit_width = (
                PREF_EDIT_WIDTH if curses.COLS > PREF_EDIT_WIDTH else curses.COLS - 2
            )


if __name__ == "__main__":
    curses.wrapper(main)
