import curses
from curses import textpad
import logging

from src.tui.utils import (
    KEY_ENTER,
    KEY_EXIT,
    border,
    show_cursor,
)


class GrowableTextbox:
    def __init__(
        self,
        height: int,
        width: int,
        y: int,
        x: int,
        title: str = "",
        text: str = "",
    ):
        self.height = height
        self.width = width
        self.y = y
        self.x = x
        self.title = title

        self.cur = 0
        self._win = curses.newwin(height, width, y, x)
        self._win.addstr(0, 0, text)
        self._border_win = border(self._win, title=self.title)
        self._textbox = textpad.Textbox(self._win, insert_mode=True)
        self._exit = False
        self._buffer = text

    def edit(self) -> str:
        with show_cursor():
            text = self._textbox.edit(self.validator).strip().replace("\n", "")
        logging.debug(f"{text=} {self._buffer=} {self._need_redraw()=}")
        if not self._need_redraw():
            self.destroy()
            return self._buffer

        logging.debug("Redrawing edit window")
        self.height += 1
        self.destroy()

        self._win = curses.newwin(self.height, self.width, self.y, self.x)
        self._border_win = border(self._win, title=self.title)
        self._win.addstr(0, 0, self._buffer)
        self._textbox = textpad.Textbox(self._win)

        self._win.refresh()
        self._border_win.refresh()

        return self.edit()

    def destroy(self) -> None:
        self._border_win.clear()
        self._border_win.refresh()
        self._win.clear()
        self._win.refresh()

    # TODO: Handle Ctrl + A, Ctrl + E, etc.
    def validator(self, ch: int) -> int:
        if ch == curses.KEY_BACKSPACE:
            self.cur = max(self.cur - 1, 0)
            self._buffer = self._buffer[:-1]
        elif ch == KEY_ENTER:
            self._exit = True
            return KEY_EXIT
        elif ch == curses.KEY_RESIZE:
            logging.debug(f"RESIZE: '{self._buffer}'")
            if self._buffer == "":
                self._exit = True
            return KEY_EXIT
        elif 32 <= ch <= 126:
            logging.debug(f"{ch=} {chr(ch)=}")
            self.cur += 1
            self._buffer += chr(ch)
        if self.cur >= (self.width * self.height) - 1:
            return KEY_EXIT
        return ch

    def _need_redraw(self) -> bool:
        return not self._exit or self.cur >= (self.width * self.height) - 1

    @property
    def submitted(self) -> bool:
        return self._exit
