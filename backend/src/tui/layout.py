from contextlib import contextmanager
from dataclasses import dataclass
from fractions import Fraction
from types import TracebackType
from typing import Generator, NamedTuple, Self


class Rect(NamedTuple):
    height: int
    width: int
    y: int
    x: int


class Point(NamedTuple):
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
        rows: int,
        cols: int,
        # TODO: maybe remove these
        y: int = 0,
        x: int = 0,
    ) -> None:
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
        # FIXME: handle child_min_width = None
        child_min_width: int | None = None,
        child_min_height: int | None = None,
        **kwargs,
    ) -> bool:
        total_width = self.cols - (screen_padding * 2 + (columns - 1) * spacing)
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
        screen_padding: int = 0,
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
        assert len(self._state_stack) > 0
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
    def horizontal(self, columns: int, **kwargs) -> Generator[Self, None, None]:
        if self._begin_horizontal(columns=columns, **kwargs):
            try:
                yield True
            finally:
                self._end_horizontal(**kwargs)
        else:
            yield False

    @contextmanager
    def vertical(self, rows: int, **kwargs) -> Generator[Self, None, None]:
        if self._begin_vertical(rows=rows, **kwargs):
            try:
                yield True
            finally:
                self._end_vertical(**kwargs)
        else:
            yield False
