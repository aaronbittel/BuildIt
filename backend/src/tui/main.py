import _curses
import curses
import logging
from contextlib import suppress
from curses import A_NORMAL, KEY_RESIZE

from src.tui.stage_view import Stage
from src.tui.stage_view_list import StageViewList
from src.tui.utils import (
    border,
    get_input,
    hide_cursor,
    title,
)

logging.basicConfig(
    filename="app.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


GREEN_ON_BLACK = 1
BLACK_ON_GREEN = 2
YELLOW_ON_BLACK = 3

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
        logging.debug(f"segment: {text[cur : cur + width]}")
        last_space_idx = text[cur : cur + width].rfind(" ")
        if last_space_idx == -1:
            logging.debug("no space found")
            lines.append(text[cur : cur + width])
            cur += width
        elif last_space_idx == 0:
            cur += 1
        else:
            logging.debug(f"space found at {last_space_idx}")
            lines.append(text[cur : cur + last_space_idx])
            cur += last_space_idx
        logging.debug(f"{lines=}")
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


def confirm(
    rows: int,
    cols: int,
    message: str,
    min_width: int = 20,
    title: str = "Confirm",
    border_color: int | None = None,
) -> bool:
    # FIXME:
    def draw_choices(win: curses.window, selected: bool = True) -> None:
        yes, no = "Yes", "No"
        confirm_space = 4
        confirm_width = len(yes) + confirm_space + len(no)  # spaces(4)
        yes_start = width // 2 - confirm_width // 2
        attr = curses.A_REVERSE if selected else A_NORMAL
        win.addstr(height - 2, yes_start, yes, attr)
        attr = curses.A_REVERSE if not selected else A_NORMAL
        win.addstr(height - 2, yes_start + len(yes) + confirm_space, no, attr)

    def draw_choice(win: curses.window) -> None:
        yes, no = "Yes", "No"
        confirm_space = 4
        confirm_width = len(yes) + confirm_space + len(no)  # spaces(4)
        yes_start = width // 2 - confirm_width // 2
        win.addstr(height - 2, yes_start, yes)
        win.addstr(height - 2, yes_start + len(yes) + confirm_space, no)

    split_width = max(cols // 2, min_width)
    lines = split_text_into_lines(text=message, width=split_width)
    height = len(lines) + 2 + 1 + 1  # space(2) + Yes/No(1) + space(1)

    maxlen = max(map(len, lines))
    width = maxlen + 2

    win = curses.newwin(
        height,
        width,
        rows // 2 - height // 2,
        cols // 2 - width // 2,
    )
    color = border_color if border_color is not None else GREEN_ON_BLACK
    border_win = border(win, title, color=color)

    for i, line in enumerate(lines, start=1):
        win.addstr(i, 1, line)

    draw_choices(win)
    win.refresh()

    selected = True

    while True:
        key = win.getch()

        if key in map(ord, ("l", "L", "h", "H")):
            selected = not selected
            draw_choices(win, selected)
            win.refresh()
        elif key == ord("\n"):
            break
        elif key in map(ord, ("y", "Y")):
            selected = True
            break
        elif key in map(ord, ("n", "N", "q", "Q")):
            selected = False
            break
        elif key == KEY_RESIZE:
            logging.info("RESIZE in DIALOG")

    draw_choice(win)
    win.refresh()
    curses.napms(40)
    draw_choices(win, selected)
    win.refresh()
    curses.napms(120)
    win.clear()
    win.refresh()
    border_win.clear()
    border_win.refresh()
    return selected


@hide_cursor
def main(stdscr: curses.window):
    curses.start_color()
    curses.init_pair(GREEN_ON_BLACK, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(BLACK_ON_GREEN, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(YELLOW_ON_BLACK, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    stdscr.keypad(True)

    stdscr.clear()
    stdscr.refresh()

    rows, cols = stdscr.getmaxyx()

    title_text = "Buildit! - Tui"
    title(stdscr, cols=cols, text=title_text)

    stage_view_list = StageViewList(y=3, stages=stages, cols=cols, min_width=30)

    alternate_stage_view_list = StageViewList(
        y=2,
        stages=[
            Stage(name="Backlog", tasks=[]),
            Stage(name="In Progress", tasks=[]),
            Stage(name="Done", tasks=[]),
        ],
        cols=cols,
    )

    def calc_edit_width(cols: int, min_width: int = 10) -> int:
        return max(int(cols * 0.75), 10)

    edit_width = calc_edit_width(cols)

    running = True
    help_open = False
    popup_win: curses.window | None = None

    textbox_text = ""

    while running:
        stage_view_list.draw()

        key = stdscr.getch()

        if key == ord("q"):
            running = False
        elif key == ord("c"):
            choice = confirm(
                rows=rows,
                cols=cols,
                message="What about a really really long long longer Question?qqqqqq",
                border_color=YELLOW_ON_BLACK,
                title="[TEST CONFIRM DIALOG]",
            )
            stage_view_list.draw(force=True)
            logging.debug(f"confirm: {choice}")
        elif key == ord("?"):
            help(rows, cols, help_open=help_open)
            help_open = not help_open
        elif key == ord("a"):
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
        elif key == ord("\n"):
            if confirm(rows, cols, message="Create new StageView?"):
                stage_view_list.clear()
                stage_view_list, alternate_stage_view_list = (
                    alternate_stage_view_list,
                    stage_view_list,
                )
                stage_view_list.selected.blink(
                    color_pair=BLACK_ON_GREEN, duration_ms=120
                )
            stage_view_list.draw(force=True)
        elif key == curses.KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            title(stdscr, cols=cols, text=title_text)
            stage_view_list.resize(cols)
            edit_width = calc_edit_width(cols)


if __name__ == "__main__":
    curses.wrapper(main)
