from contextlib import contextmanager, suppress
import curses
import logging
import _curses
from dataclasses import dataclass
from types import TracebackType
from typing import Generator, NamedTuple, Self
from fractions import Fraction

from data import Board, Stage, Task

logging.basicConfig(filename="app.log", level=logging.ERROR, filemode="w")

ELLIPSIS = "…"


class Rect(NamedTuple):
    height: int
    width: int
    y: int
    x: int


@dataclass
class LayoutState:
    last: bool = False

    next_cursor_x: Fraction = Fraction()
    next_cursor_y: int = 0

    columns: int = 0
    rows: int = 0

    screen_padding: int = 1
    spacing: int = 0

    total_width: int = 0
    total_height: int = 0
    child_height: int = 0
    frac_width_per_child: Fraction = Fraction()
    freq_child_min_width: Fraction = Fraction()
    freq_child_min_height: Fraction = Fraction()
    max_content_height: int = 0
    max_content_width: int = 0

    use_vertical_layout: bool = False


class Layout:
    def __init__(
        self,
        win: curses.window,
        rows: int,
        cols: int,
        # TODO: maybe remove these
        y: int = 0,
        x: int = 0,
    ) -> None:
        self.win = win
        self.rows = rows
        self.cols = cols
        self.y = y
        self.x = x

        self._state_stack: list[LayoutState] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        self._end()

    def _begin_horizontal(
        self,
        screen_padding: int = 0,
        spacing: int = 0,
        columns: int = 1,
        child_min_width: int | None = None,
        child_min_height: int | None = None,
        **kwargs,
    ) -> bool:
        total_width = self.cols - (screen_padding * 2 + (columns - 1) * spacing)
        # TODO: use floats
        frac_width_per_child = Fraction(total_width, columns)

        if child_min_width is not None and frac_width_per_child < child_min_width:
            return False

        self._state_stack.append(
            LayoutState(
                next_cursor_x=screen_padding,
                next_cursor_y=self.y,
                spacing=spacing,
                screen_padding=screen_padding,
                total_width=total_width,
                frac_width_per_child=frac_width_per_child,
                columns=columns,
                freq_child_min_width=Fraction(child_min_width),
                freq_child_min_height=Fraction(child_min_height)
                if child_min_height
                else None,
            )
        )
        return True

    def _end_horizontal(self, after_spacing: int = 0, **kwargs) -> None:
        layout_state = self._state_stack.pop()

        self.y = (
            layout_state.next_cursor_y + layout_state.max_content_height + after_spacing
        )

        self.x = 0

    def _begin_vertical(
        self,
        screen_padding: int = 1,
        spacing: int = 0,
        rows: int = 1,
        child_min_width: int | None = None,
        child_min_height: int | None = None,
        **kwargs,
    ) -> None:
        available_width_per_child = self.cols - 2 * screen_padding

        if available_width_per_child < child_min_width:
            return False

        self._state_stack.append(
            LayoutState(
                next_cursor_y=self.y,
                next_cursor_x=screen_padding,
                screen_padding=screen_padding,
                spacing=spacing,
                rows=rows,
                freq_child_min_width=child_min_width,
                freq_child_min_height=child_min_height,
                frac_width_per_child=available_width_per_child,
                use_vertical_layout=True,
            )
        )

        return True

    def _end_vertical(self, after_spacing: int = 0, **kwargs) -> None:
        layout_state = self._state_stack.pop()

        self.y = layout_state.next_cursor_y + after_spacing
        self.x = 0

    def next_rect(self, height: int) -> Rect:
        layout_state = self._state_stack[-1]

        last = False

        if layout_state.use_vertical_layout:
            layout_state.rows -= 1
            last = layout_state.rows == 0
        else:
            layout_state.columns -= 1
            last = layout_state.columns == 0

        y = layout_state.next_cursor_y
        frac_x = layout_state.next_cursor_x

        frac_width = layout_state.frac_width_per_child

        # for horizontal layout
        layout_state.max_content_height = max(layout_state.max_content_height, height)

        spacing = 0 if last else layout_state.spacing
        if layout_state.use_vertical_layout:
            layout_state.next_cursor_y += height + spacing
        else:
            layout_state.next_cursor_x += frac_width + layout_state.spacing

        target_x = int(frac_x + frac_width)
        x = int(frac_x)
        width = target_x - x
        return Rect(
            y=y,
            x=x,
            height=height,
            width=width,
        )

    def _begin(self, y: int = 0, x: int = 0) -> None:
        self.cursor_y = y
        self.cursor_x = x

    def _end(self) -> None: ...

    @contextmanager
    def horizontal(self, **kwargs) -> Generator[Self, None, None]:
        if self._begin_horizontal(**kwargs):
            try:
                yield True
            finally:
                self._end_horizontal(**kwargs)
        else:
            yield False

    @contextmanager
    def vertical(self, **kwargs) -> Generator[Self, None, None]:
        if self._begin_vertical(**kwargs):
            try:
                yield True
            finally:
                self._end_vertical(**kwargs)
        else:
            yield False


def box(
    rect: Rect,
    title: str,
    content: list[str],
    selected: int,
    highlighted: bool = False,
):
    height, width, y, x = rect
    win = curses.newwin(height, width, y, x)

    # Draw Border
    color = curses.color_pair(1) if highlighted else curses.color_pair(0)
    win.addch(0, 0, curses.ACS_ULCORNER, color)
    win.hline(0, 1, curses.ACS_HLINE, width - 2, color)
    win.addch(0, width - 1, curses.ACS_URCORNER, color)

    for y in range(1, height + 1):
        with suppress(_curses.error):
            win.addch(y, 0, curses.ACS_VLINE, color)
            win.addch(y, width - 1, curses.ACS_VLINE, color)

    win.addch(height - 1, 0, curses.ACS_LLCORNER, color)
    win.hline(height - 1, 1, curses.ACS_HLINE, width - 2, color)
    with suppress(_curses.error):
        win.addch(height - 1, width - 1, curses.ACS_LRCORNER, color)

    # Draw Content
    if len(title) > width:
        title = title[: width - 1] + ELLIPSIS

    if width > 4:
        win.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        for i, line in enumerate(content):
            if len(line) > width - 4:
                line = line[: width - 4 - 1] + ELLIPSIS
            with suppress(_curses.error):
                win.addstr(i + 1, 2, line)
            if highlighted:
                if i == selected:
                    win.chgat(i + 1, 1, width - 2, curses.color_pair(2))
    win.refresh()


def text(rect: Rect, s: str, attr: int = 0, centered: bool = True) -> None:
    height, width, y, x = rect
    height = height if height is not None else 1
    win = curses.newwin(height, width, y, x)
    win.bkgd(" ", curses.color_pair(3))

    if len(s) > width:
        s = s[: width - 1] + ELLIPSIS

    start_x = width // 2 - len(s) // 2 if centered else 0
    with suppress(_curses.error):
        win.addstr(0, start_x, s, attr)

    win.refresh()


def board_view(layout: Layout, board: Board) -> None:
    for i, stage in enumerate(board.stages):
        content = list(map(lambda t: t.name, stage.tasks))
        rect = layout.next_rect(height=max(len(content) + 2, 5))
        highlighted = i == board.selected
        box(
            rect=rect,
            title=stage.title,
            content=content,
            selected=board.stage.selected,
            highlighted=highlighted,
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
    layout = Layout(stdscr, rows, cols)

    stage_min_width = 25
    logging.error(f"{rows=} {cols=}")

    while True:
        stdscr.erase()
        stdscr.refresh()

        with layout as l:
            with l.vertical(after_spacing=1, child_min_width=5) as ok:
                if ok:
                    rect = layout.next_rect(height=1)
                    text(
                        rect,
                        board.title,
                        attr=curses.A_BOLD | curses.A_UNDERLINE,
                    )

            with l.horizontal(
                screen_padding=1,
                spacing=2,
                after_spacing=2,
                child_min_width=stage_min_width,
                columns=len(board.stages),
            ) as ok:
                if ok:
                    board_view(layout, board)

            if not ok:
                with l.vertical(
                    spacing=0,
                    child_min_width=stage_min_width,
                    rows=len(board.stages),
                ) as ok:
                    if ok:
                        board_view(layout, board)

            if not ok:
                pass

        key = stdscr.getch()

        if key == ord("q"):
            break
        elif key == ord("j"):
            board.stage.next()
        elif key == ord("k"):
            board.stage.prev()
        elif key == ord("\t"):
            board.next()
        elif key == ord("\n"):
            board = board.goto_next_board(
                stage_idx=board.selected, task_idx=board.stage.selected
            )
        elif key == 27:
            board = board.goto_prev_board()
        elif key == curses.KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            logging.error(f"{rows=} {cols=}")
        layout = Layout(stdscr, rows, cols)


if __name__ == "__main__":
    curses.wrapper(main)
