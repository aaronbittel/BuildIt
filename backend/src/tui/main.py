from contextlib import contextmanager, suppress
from curses import KEY_RESIZE, newwin, wrapper, window, textpad
import curses
import _curses
from collections import namedtuple
from functools import wraps

ROUNDED_TOPLEFT = "╭"
ROUNDED_TOPRIGHT = "╮"
ROUNDED_BOTTOMRIGHT = "╯"
ROUNDED_BOTTOMLEFT = "╰"
VERTICAL_BAR = "│"
HORIZONTAL_BAR = "─"


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
    Stage(name="In Progress", tasks=["Task 1", "Task 2"]),
    Stage(name="Done", tasks=["Finished 1", "Finished 2", "Finished 3", "Another One"]),
]


class StageView:
    def __init__(
        self,
        name: str,
        tasks: list[str],
        y: int,
        x: int,
        min_height: int = 4,
        width: int = 20,
        highlighted: bool = False,
    ) -> None:
        self.name = name
        self.tasks = tasks
        self.min_height = min_height
        self.content_height = max(len(tasks), min_height)
        self.view_height = self.content_height + 2

        self._win = curses.newwin(self.view_height, width, y, x)
        self.highlighted = highlighted
        self.selected = 0

    def _calculate_heights(self) -> None:
        self.content_height = max(len(self.tasks), self.min_height)
        self.view_height = self.content_height + 2

    def resize(self, y: int, x: int) -> None:
        self._win.clear()
        self._win.refresh()

        self._win = curses.newwin(self.view_height, self.width, y, x)

    def draw(self) -> None:
        self._win.clear()
        self._draw_border()

        self._win.addstr(0, (self.width - len(self.name)) // 2, self.name)
        for i, task in enumerate(self.tasks):
            self._win.addstr(i + 1, 2, task)
            if self.highlighted:
                if i == self.selected:
                    self._win.chgat(i + 1, 1, self.width - 2, curses.color_pair(2))

        self._win.refresh()

    def _draw_border(self) -> None:
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
        self.tasks.append(task)
        if len(self.tasks) > self.content_height:
            self._calculate_heights()
            self._win = curses.newwin(self.view_height, self.width, self.y, self.x)

    def next(self) -> None:
        self.selected = min(self.selected + 1, len(self.tasks) - 1)

    def prev(self) -> None:
        self.selected = max(self.selected - 1, 0)

    def update(self, task: str) -> None:
        self.tasks[self.selected] = task

    @property
    def text(self) -> str:
        return self.tasks[self.selected]

    @property
    def height(self) -> int:
        return self._win.getmaxyx()[0]

    @property
    def width(self) -> int:
        return self._win.getmaxyx()[1]

    @property
    def y(self) -> int:
        return self._win.getbegyx()[0]

    @property
    def x(self) -> int:
        return self._win.getbegyx()[1]


def border(win: window, title: str | None = None) -> window:
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
    y: int, x: int, height: int = 1, width: int = 25, text: str | None = None
) -> str:
    def exit_on_enter(ch: int) -> int:
        if ch == ord("\n"):
            return 7
        return ch

    win = curses.newwin(height, width, y, x)
    if text is not None:
        win.addstr(0, 0, text)
    border_win = border(win, title="Add" if text is None else "Edit")
    textbox = textpad.Textbox(win, insert_mode=True)

    with show_cursor():
        text = textbox.edit(exit_on_enter).strip()

    border_win.clear()
    win.clear()
    border_win.refresh()
    win.refresh()
    return text


class StageViewList:
    def __init__(self, y: int, stages: list[Stage], stage_width: int = 25) -> None:
        assert len(stages) > 0

        self.y = y
        self.stages = stages
        self.stage_width = stage_width

        content_width = stage_width * len(stages)
        space_left = curses.COLS - content_width
        space_len = space_left // (len(stages) + 1)

        self.stage_views: list[StageView] = [
            StageView(
                name=s.name,
                tasks=s.tasks,
                y=y,
                x=space_len + i * (stage_width + space_len),
                width=stage_width,
            )
            for i, s in enumerate(stages)
        ]

        self._selected = 0
        self.selected.highlighted = True
        self._dirty_views: set[StageView] = set(self.stage_views)

    def draw(self) -> None:
        for stage in self._dirty_views:
            stage.draw()
        self._dirty_views.clear()

    def resize(self, rows: int, cols: int) -> None:
        content_width = self.stage_width * len(self.stages)
        space_left = cols - content_width
        space_len = space_left // (len(self.stages) + 1)

        for view in self.stage_views:
            view._win.clear()
            view._win.refresh()

        content_width = self.stage_width * len(self.stages)
        space_left = cols - content_width
        space_len = space_left // (len(self.stages) + 1)

        for i, view in enumerate(self.stage_views):
            if space_left >= 0:
                y = self.y
                x = space_len + i * (self.stage_width + space_len)
            else:
                if i == 0:
                    y = self.y
                else:
                    y += view.height + 1
                x = cols // 2 - view.width // 2
            view.resize(y=y, x=x)

        self._dirty_views = set(self.stage_views)

    def selected_task(self) -> str:
        return self.selected.text

    def update_task(self, task: str) -> str:
        self._dirty_views.add(self.selected)
        return self.selected.update(task)

    def add(self, task: str) -> None:
        self._dirty_views.add(self.selected)
        self.selected.add(task)

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


@contextmanager
def show_cursor():
    try:
        curses.curs_set(1)
        yield
    finally:
        curses.curs_set(0)


def debug(msg: str) -> None:
    win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
    win.addstr(msg)
    win.refresh()


def title(win: window, cols: int, text: str) -> None:
    win.move(0, 0)
    win.clrtoeol()
    win.refresh()

    win.addstr(0, cols // 2 - len(text) // 2, text, curses.A_BOLD | curses.A_UNDERLINE)


@hide_cursor
def main(stdscr: window):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)

    stdscr.keypad(True)

    stdscr.clear()
    stdscr.refresh()

    title_text = "Buildit! - Tui"
    title(stdscr, cols=curses.COLS, text=title_text)

    stage_view_list = StageViewList(
        y=2, stages=stages, stage_width=int(curses.COLS * 0.3)
    )

    edit_width = 48

    running = True

    while running:
        stage_view_list.draw()

        key = stdscr.getch()
        if key == ord("q"):
            running = False
        elif key == ord("a"):
            got = get_input(
                y=curses.LINES // 2,
                x=curses.COLS // 2 - edit_width // 2,
                width=edit_width,
            )
            stage_view_list.add(got)
        elif key == ord("e"):
            got = get_input(
                y=curses.LINES // 2,
                x=curses.COLS // 2 - edit_width // 2,
                width=edit_width,
                text=stage_view_list.selected_task(),
            )
            stage_view_list.update_task(got)
        elif key == ord("j"):
            stage_view_list.next_task()
        elif key == ord("k"):
            stage_view_list.prev_task()
        elif key == ord("\t"):
            stage_view_list.next_stage()
        elif key == KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            title(stdscr, cols=cols, text=title_text)
            stage_view_list.resize(rows, cols)


if __name__ == "__main__":
    wrapper(main)
