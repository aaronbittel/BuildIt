import curses
import logging

from data import Board, Stage, Task

from src.tui.components import box, text
from src.tui.layout import Layout

logging.basicConfig(filename="app.log", level=logging.ERROR, filemode="w")


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

    stage_min_width = 25

    logging.error(f"{rows=} {cols=}")

    while True:
        stdscr.erase()
        stdscr.refresh()

        with Layout(stdscr, rows, cols) as layout:
            with layout.vertical(rows=1, after_spacing=1, child_min_width=5) as ok:
                if ok:
                    display_title(layout=layout, title=board.title)

            with layout.horizontal(
                screen_padding=1,
                spacing=2,
                after_spacing=2,
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


if __name__ == "__main__":
    curses.wrapper(main)
