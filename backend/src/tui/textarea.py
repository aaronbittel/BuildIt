import curses

from src.tui.layout import Rect


def text_field(stdscr: curses.window, rect: Rect, text: str, key: int) -> str:
    height, width, y, x = rect
    stdscr.addstr(y, x, f"+{'-' * (width - 2)}+")
    stdscr.addstr(y + height - 1, x, f"+{'-' * (width - 2)}+")
    for row in range(1, height - 1):
        stdscr.addstr(y + row, x, "|")
        stdscr.addstr(y + row, x + width - 1, "|")

    stdscr.addstr(y + 1, x + 2, text)

    if key == -1:
        return text

    if 32 <= key <= 126:
        text += chr(key)
    elif key == curses.KEY_BACKSPACE and len(text) > 0:
        text = text[:-1]

    return text


def main(stdscr: curses.window):
    curses.curs_set(1)
    stdscr.nodelay(True)
    stdscr.clear()

    height, width = stdscr.getmaxyx()

    text = "Hello, World"
    key = -1

    while True:
        stdscr.erase()
        text = text_field(
            stdscr, Rect(height=3, width=len(text) + 20, y=5, x=5), text=text, key=key
        )

        key = stdscr.getch()
        if key == 27:
            break

        stdscr.noutrefresh()

        curses.doupdate()
        # break

    # time.sleep(10)


curses.wrapper(main)
