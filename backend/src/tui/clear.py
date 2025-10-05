import curses
import logging
from curses import wrapper

logging.basicConfig(filename="text.log", filemode="w", level=logging.DEBUG)


def text(y: int, x: int, text: str) -> curses.window:
    height, width = 3, len(text) + 4
    win = curses.newwin(height, width, y, x)
    win.box()
    win.addstr(1, 2, text)
    return win


def main(stdscr: curses.window):
    curses.curs_set(0)
    key = None
    rows, cols = stdscr.getmaxyx()

    stdscr.timeout(int(1 / 60 * 1000))

    y, x = rows // 2, cols // 2
    win = text(y, x, "Hello, World!")

    while True:
        if key != -1:
            if key == ord("q"):
                break
            elif key == ord("j"):
                y += 1
            elif key == ord("k"):
                y -= 1
            elif key == ord("h"):
                x -= 3
            elif key == ord("l"):
                x += 3

            win.erase()
            win = text(y, x, "Hello, World!")
            win.noutrefresh()
        stdscr.noutrefresh()
        curses.doupdate()
        key = stdscr.getch()
    curses.curs_set(1)


wrapper(main)
