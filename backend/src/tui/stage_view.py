from contextlib import suppress
import curses
import logging
import utils
import _curses
from typing import NamedTuple
from src.tui.utils import ELLIPSIS


class Stage(NamedTuple):
    name: str
    tasks: list[str]


class StageView:
    def __init__(
        self,
        stage: Stage,
        min_height: int = 4,
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

    def remove(self) -> None:
        if len(self.stage.tasks) == 0:
            return
        self.stage.tasks.pop(self.selected)
        self.selected = max(self.selected - 1, 0)

    def next(self) -> None:
        self.selected = min(self.selected + 1, max(0, len(self.stage.tasks) - 1))

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
