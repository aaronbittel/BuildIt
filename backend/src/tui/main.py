import curses
from src.tui.stage_view import Stage
from src.tui.stage_view_list import StageViewList
from src.tui.utils import (
    debug,
    debug_block,
    get_input,
    hide_cursor,
    title,
)


PREF_EDIT_WIDTH = 48

# TODO: use floats for calculation for precise results
# TODO: use win.mvwin and / or win.resize instead of creating new windows (if its
# easier)
# TODO: Look into this: erase, noutrefresh, doupdate, etc.


stages = [
    Stage(name="Backlog", tasks=["Todo 1", "Todo 2", "Todo 3"]),
    Stage(name="In Progress", tasks=["Task 1", "Task 2", "Long Long Long Message"]),
    Stage(name="Done", tasks=["Finished 1", "Finished 2", "Finished 3", "Another One"]),
]


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
            x = max(cols // 2 - edit_width // 2, 1)
            got = get_input(
                y=stage_view_list.bottom + 1,
                x=x,
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
            edit_width = PREF_EDIT_WIDTH if cols - 2 > PREF_EDIT_WIDTH else cols - 2


if __name__ == "__main__":
    curses.wrapper(main)
