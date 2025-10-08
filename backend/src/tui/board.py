from __future__ import annotations

import curses
import random
from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid1

from src.tui.components import box
from src.tui.layout import Layout, Point, Rect
from src.tui.ui import Event, Id, UIContext
from src.tui.utils import KEY_ESC


class Board:
    DefaultStages = ["Backlog", "In Progress", "Done"]

    def __init__(
        self,
        title: str,
        stages: list[Stage] | None = None,
        prev_board: Board | None = None,
        id: UUID | None = None,
    ) -> None:
        self.id = id if id is not None else uuid1()
        self.title = title
        self.stages = stages if stages is not None else []
        self.prev_board = prev_board

        self.selected = 0

    @classmethod
    def default(
        cls,
        title: str,
        prev_board: Board | None = None,
        *,
        # FIXME: Remove me later
        prefilled: bool = False,
    ) -> Self:
        get_tasks = lambda: [Task(name) for name in random_tasks()] if prefilled else []
        return cls(
            title,
            stages=[Stage(t, tasks=get_tasks()) for t in Board.DefaultStages],
            prev_board=prev_board,
        )

    def goto_next_board(
        self,
        stage_idx: int,
        task_idx: int,
        *,
        # FIXME: Remove me later
        prefilled: bool = False,
    ) -> Board:
        task = self.stages[stage_idx].tasks[task_idx]
        if task.next_board is not None:
            return task.next_board

        board = Board.default(title=task.name, prev_board=self, prefilled=prefilled)
        task.next_board = board
        return board

    def goto_prev_board(self) -> Board:
        return self.prev_board if self.prev_board is not None else self

    def next(self) -> None:
        self.selected += 1
        if self.selected >= len(self.stages):
            self.selected = 0

    def prev(self) -> None:
        self.selected -= 1
        if self.selected < 0:
            self.selected = 0

    def forward_task(self) -> None:
        if self.selected == len(self.stages) - 1 or len(self.stage) == 0:
            return
        task = self.stage.pop()
        self.stages[self.selected + 1].add(task)

    def recall_task(self) -> None:
        if self.selected == 0 or len(self.stage) == 0:
            return
        task = self.stage.pop()
        self.stages[self.selected - 1].add(task)

    def add_stage(self, stage: Stage) -> None:
        self.stages.append(stage)

    def __len__(self) -> int:
        return len(self.stages)

    def __str__(self) -> str:
        def maxlen(stage: Stage) -> int:
            return max(len(stage.title), max(map(len, stage.tasks), default=0))

        def content(stage: Stage, idx: int) -> str:
            return stage.tasks[idx].name if len(stage.tasks) > idx else ""

        maxlens = [maxlen(stage) for stage in self.stages]
        total_len = sum(maxlens) + len(self.stages) - 1
        title = f"~{self.title}~"

        out = f"{title.center(total_len)}\n"

        out += " ".join(
            [stage.title.center(maxlens[i]) for i, stage in enumerate(self.stages)]
        )
        out += "\n"

        m = max(len(stage.tasks) for stage in self.stages)
        for i in range(m):
            out += " ".join(
                content(stage, i).ljust(maxlens[j])
                for j, stage in enumerate(self.stages)
            )
            out += "\n"

        return out

    @property
    def stage(self) -> Stage:
        return self.stages[self.selected]


@dataclass
class Task:
    name: str
    next_board: Board | None = None

    def __len__(self) -> int:
        return len(self.name)


class Stage:
    def __init__(self, title: str, tasks: list[Task] | None = None) -> None:
        self.title = title
        self.tasks = tasks if tasks is not None else []
        self.selected = 0

    def add(self, task: Task) -> None:
        self.tasks.append(task)

    def pop(self) -> Task:
        task = self.tasks.pop(self.selected)
        if self.selected >= len(self.tasks):
            self.selected = max(self.selected - 1, 0)
        return task

    def next_task(self) -> None:
        if self.selected + 1 < len(self.tasks):
            self.selected += 1

    def prev_task(self) -> None:
        if self.selected - 1 >= 0:
            self.selected -= 1

    def move_task(self, dir: int) -> None:
        if len(self.tasks) == 0:
            return

        old_pos = self.selected
        new_pos = old_pos + dir
        if new_pos < 0 or new_pos >= len(self.tasks):
            return

        text = self.tasks.pop(old_pos)
        self.tasks.insert(new_pos, text)
        self.selected = new_pos

    def __getitem__(self, idx: int) -> Task:
        if idx >= len(self.tasks):
            raise IndexError("stage index out of range")
        return self.tasks[idx]

    def __len__(self) -> int:
        return len(self.tasks)

    def __repr__(self) -> str:
        task_repr = "[]"
        if self.tasks:
            task_repr = "["
            for task in self.tasks:
                task_repr += f"\n\tTask(name={task.name}),"
            task_repr += "\n]"
        out = f"Stage(title={self.title}, tasks={task_repr})"
        return out

    @property
    def task(self) -> Task:
        return self.tasks[self.selected]


def board_widget(
    ctx: UIContext, board: Board, id: Id, stage_min_width: int
) -> Event | None:
    if ctx.uistate.active_id is None:
        ctx.uistate.active_id = id

    if len(board) > 0:
        with ctx.layout.horizontal(
            screen_padding=1,
            spacing=2,
            after_spacing=1,
            child_min_width=stage_min_width,
            columns=len(board),
        ) as h_ok:
            if h_ok:
                board_rects = _board_view(ctx.stdscr, ctx.layout, board)
                board_is_showing = True

            if not h_ok:
                with ctx.layout.vertical(
                    screen_padding=1,
                    spacing=0,
                    child_min_width=stage_min_width,
                    rows=len(board),
                ) as v_ok:
                    if v_ok:
                        board_rects = _board_view(ctx.stdscr, ctx.layout, board)
                    board_is_showing = v_ok

    event: Event = None

    key = ctx.uistate.key
    if ctx.uistate.active_id == id and not ctx.uistate.key_consumed and key != -1:
        ctx.uistate.key_consumed = True
        if key == ord("j"):
            if len(board) > 0:
                board.stage.next_task()
        elif key == ord("k"):
            if len(board) > 0:
                board.stage.prev_task()
        elif key == ord("n"):
            if len(board) > 0:
                board.forward_task()
        elif key == ord("p"):
            board.recall_task()
        elif key == ord("a"):
            if len(board) > 0:
                event = "Add Task"
        elif key == ord("e"):
            if len(board) > 0:
                if len(board.stage.tasks) > 0:
                    event = ("Edit Task", {"prefill": board.stage.task.name})
                else:
                    event = "Add Task"
        elif key == ord("x"):
            if len(board) > 0 and len(board.stage) > 0:
                board.stage.pop()
        elif key == ord("s"):
            if (
                len(board) > 0
                and len(board.stage) > 0
                and board_is_showing
                and board_rects[board.selected].width - 4 < len(board.stage.task.name)
            ):
                rect = board_rects[board.selected]
                y_offset = board.stage.selected
                # fmt: off
                event = (
                    "Show Hover",
                    {
                        "position": Point(
                            y=rect.y + 1 + y_offset,  # border(1)
                            x=rect.x + 2,             # border(1) + padding(1)
                        ),
                        "text": board.stage.task.name,
                    },
                )
                # fmt: on
        elif key == ord("J"):
            if len(board) > 0:
                board.stage.move_task(1)
        elif key == ord("K"):
            if len(board) > 0:
                board.stage.move_task(-1)
        elif key == ord("A"):
            event = "Add Stage"
        elif key == ord("E"):
            if len(board) > 0:
                event = ("Edit Stage", {"prefill": board.stage.title})
            else:
                event = "Add Stage"
        elif key == ord("X"):
            # TODO: Add confirmation
            if len(board) > 0:
                board.stages.pop(board.selected)
                if board.selected >= len(board):
                    board.selected -= 1
        elif key == ord("\t"):
            board.next()
        elif key == curses.KEY_BTAB:
            board.prev()
        elif key == ord("\n"):
            if len(board.stage) > 0:
                board = board.goto_next_board(
                    stage_idx=board.selected,
                    task_idx=board.stage.selected,
                    prefilled=False,
                )
                event = ("Update Board", {"new_board": board})
        elif key == KEY_ESC:
            board = board.goto_prev_board()
            event = ("Update Board", {"new_board": board})
    return event


def _board_view(stdscr: curses.window, layout: Layout, board: Board) -> list[Rect]:
    rects: list[Rect] = []
    for i, stage in enumerate(board.stages):
        content = list(map(lambda t: t.name, stage.tasks))
        rect = layout.next_rect(height=max(len(content) + 2, 5))
        highlighted = i == board.selected
        box(
            stdscr,
            rect=rect,
            title=stage.title,
            lines=content,
            selected=board.stage.selected,
            highlighted=highlighted,
            rounded=False,
        )
        rects.append(rect)
    return rects


def random_tasks() -> list[str]:
    tasks = [
        "Write report",
        "Fix login bug",
        "Update README",
        "Refactor API",
        "Test payment flow",
        "Design landing page",
        "Deploy staging",
        "Review PR #42",
        "Optimize database",
        "Plan sprint backlog",
        "Write unit tests",
        "Clean up code",
        "Update dependencies",
        "Prepare presentation",
        "Document endpoints",
    ]

    count = random.randint(2, 5)
    return random.sample(tasks, k=min(count, len(tasks)))
