import _curses
import curses
import logging
from contextlib import suppress
from curses import KEY_BACKSPACE, KEY_RESIZE, textpad

from src.tui.stage_view import Stage
from src.tui.stage_view_list import StageViewList
from src.tui.utils import (
    KEY_ENTER,
    KEY_EXIT,
    border,
    get_input,
    hide_cursor,
    show_cursor,
    title,
)

logging.basicConfig(
    filename="app.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


PREF_EDIT_WIDTH = 48

# TODO: use floats for calculation for precise results
# TODO: use win.mvwin and / or win.resize instead of creating new windows (if its
# easier)
# TODO: Look into this: erase, noutrefresh, doupdate, etc.


stages = [
    Stage(
        name="Backlog",
        tasks=[
            "use floats for calculation for precise results",
            "use win.mvwin and / or win.resize instead of creating new windows (if its easier)",
            "Look into this: erase, noutrefresh, doupdate, etc.",
        ],
    ),
    Stage(name="In Progress", tasks=["Task 1", "Task 2", "Long Long Long Message"]),
    Stage(name="Done", tasks=["Finished 1", "Finished 2", "Finished 3", "Another One"]),
]


def help(rows: int, cols: int, *, help_open: bool) -> None:
    content = [
        "?  Toggle Help",
        "q  Quit",
        "a  Add Task",
        "e  Edit Selected Task",
        "j  Next Task",
        "k  Previous Task",
        "x  Remove Selected Task",
        "n  Move Task Forward",
        "p  Move Task Back",
        "J  Move Task Down",
        "K  Move Task Up",
        "E  Edit Current Stage",
        "N  Add New Stage",
        "X  Remove Current Stage",
        "Tab        Next Stage",
        "Shift+Tab  Previous Stage",
    ]

    maxlen = max(map(len, content))

    win = curses.newwin(
        len(content) + 1, maxlen + 1, rows - len(content), cols // 2 - maxlen // 2
    )

    if not help_open:
        for i, line in enumerate(content):
            win.addstr(i, 0, line)
    else:
        win.clear()
    win.refresh()


def split_text_into_lines(text: str, width: int) -> list[str]:
    lines: list[str] = []
    cur = 0
    while cur + width < len(text):
        last_space_idx = text[cur : cur + width].rfind(" ")
        if last_space_idx == -1:
            lines.append(text[cur : cur + width])
            cur += width
        else:
            lines.append(text[cur : cur + last_space_idx])
            cur += last_space_idx
    if cur < len(text):
        lines.append(text[cur:])
    return list(map(lambda s: s.strip(), lines))


def popup(
    cursor_y: int, cursor_x: int, max_width: int, text: str, rows: int, cols: int
) -> tuple[curses.window, curses.window]:
    lines = split_text_into_lines(text, max_width)
    width = max(map(len, lines))

    if cursor_y - len(lines) - 2 >= 0:  # border (2)
        y = cursor_y - len(lines) - 1  # only bborder(1)
    else:
        y = cursor_y + 2

    win = curses.newwin(len(lines), width, y, cursor_x)
    border_win = border(win)
    border_win.refresh()
    for i, line in enumerate(lines):
        with suppress(_curses.error):
            win.addstr(i, 0, line)
    win.refresh()
    return win, border_win


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
        logging.info(f"{text=} {self._buffer=} {self._need_redraw()=}")
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
        if ch == KEY_BACKSPACE:
            self.cur = max(self.cur - 1, 0)
            self._buffer = self._buffer[:-1]
        elif ch == KEY_ENTER:
            self._exit = True
            return KEY_EXIT
        elif ch == KEY_RESIZE:
            logging.info(f"RESIZE: '{self._buffer}'")
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

    edit_width = (
        PREF_EDIT_WIDTH if curses.COLS - 2 > PREF_EDIT_WIDTH else curses.COLS - 2
    )

    running = True
    help_open = False
    popup_win: curses.window | None = None

    textbox_text = ""

    while running:
        stage_view_list.draw()

        key = stdscr.getch()

        if key == ord("q"):
            running = False
        elif key == ord("?"):
            rows, cols = stdscr.getmaxyx()
            help(rows, cols, help_open=help_open)
            help_open = not help_open
        elif key == ord("a"):
            _, cols = stdscr.getmaxyx()
            textbox = GrowableTextbox(
                height=1,
                width=edit_width,
                y=stage_view_list.bottom + 1,
                x=cols // 2 - edit_width // 2,
                title="Add Task",
                text=textbox_text,
            )
            got = textbox.edit()
            textbox_text = got
            if textbox.submitted and got != "":
                stage_view_list.add_task(got)
                textbox_text = ""
        elif key == ord("e"):
            # FIXME: handle this better
            if len(stage_view_list.selected.stage.tasks) == 0:
                continue
            _, cols = stdscr.getmaxyx()
            x = max(cols // 2 - edit_width // 2, 1)
            got = get_input(
                y=stage_view_list.bottom + 1,
                x=x,
                width=edit_width,
                text=stage_view_list.selected_task(),
                title="Edit Task",
            )
            if got != "":
                stage_view_list.update_task(got)
        elif key == ord("j"):
            stage_view_list.next_task()
        elif key == ord("k"):
            stage_view_list.prev_task()
        elif key == ord("x"):
            stage_view_list.remove_task()
        elif key == ord("n"):
            stage_view_list.move_task_forward()
        elif key == ord("p"):
            stage_view_list.move_task_back()
        elif key == ord("J"):
            stage_view_list.move_task(1)
        elif key == ord("K"):
            stage_view_list.move_task(-1)
        elif key == ord("E"):
            _, cols = stdscr.getmaxyx()
            x = max(cols // 2 - edit_width // 2, 1)
            got = get_input(
                y=stage_view_list.bottom + 1,
                x=x,
                width=edit_width,
                text=stage_view_list.selected.stage.name,
                title="Edit Stage",
            )
            if got != "":
                stage_view_list.edit_stage(got)
        elif key == ord("N"):
            _, cols = stdscr.getmaxyx()
            x = max(cols // 2 - edit_width // 2, 1)
            got = get_input(
                y=stage_view_list.bottom + 1,
                x=x,
                width=edit_width,
                title="Add Stage",
            )
            if got != "":
                stage_view_list.add_stage(got)
        elif key == ord("X"):
            stage_view_list.remove_stage()
        elif key == ord("s"):
            if popup_win is None:
                logging.debug("Drawing popup")
                if not stage_view_list.selected.selected_fit:
                    rows, cols = stdscr.getmaxyx()
                    cursor_y, cursor_x = stage_view_list.selected.selected_position
                    popup_win, border_win = popup(
                        cursor_y=cursor_y,
                        cursor_x=cursor_x,
                        max_width=max(
                            int(cols * 0.65), stage_view_list.selected.width - 3
                        ),
                        text=stage_view_list.selected.text,
                        rows=rows,
                        cols=cols,
                    )
            else:
                logging.debug("Clearing popup")
                popup_win.clear()
                popup_win.refresh()
                border_win.clear()
                border_win.refresh()
                popup_win = None
                stage_view_list.draw(force=True)
        elif key == ord("\t"):
            stage_view_list.next_stage()
        elif key == curses.KEY_BTAB:
            stage_view_list.prev_stage()
        elif key == curses.KEY_RESIZE:
            _, cols = stdscr.getmaxyx()
            title(stdscr, cols=cols, text=title_text)
            stage_view_list.resize(cols)
            edit_width = PREF_EDIT_WIDTH if cols - 2 > PREF_EDIT_WIDTH else cols - 2


if __name__ == "__main__":
    curses.wrapper(main)
