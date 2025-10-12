from src.tui.layout import Point
from src.tui.textfield import _idx_to_cursor
from src.tui.utils import split_text_into_lines


def test(input: str, idx: int, want: Point, width: int = 5):
    print(f"'{input=}'")
    lines, skipped = split_text_into_lines(input, width=width)
    got = _idx_to_cursor(idx=idx - skipped, lines=lines, width=width)
    if got != want:
        print("\tlines", lines)
        print(f"\texpected {want}, but got {got}")
        return -1
    else:
        print("SUCCESS!")


test(input="abcde", idx=5, want=Point(y=0, x=5))
test(input="a bcd", idx=5, want=Point(y=0, x=5))
test(input="abcdef", idx=6, want=Point(y=1, x=1))
test(input="a bcde", idx=6, want=Point(y=1, x=4))
test(input="abcde fghij", idx=11, want=Point(y=1, x=5))
test(input="abcdefghij", idx=10, want=Point(y=1, x=5))
