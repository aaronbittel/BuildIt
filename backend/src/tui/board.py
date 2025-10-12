from __future__ import annotations

import random
from contextlib import suppress
from dataclasses import dataclass, field
from typing import ClassVar, Iterator, Self
from uuid import UUID, uuid4


@dataclass
class Board:
    DefaultStages: ClassVar = ["Backlog", "In Progress", "Done"]

    title: str
    id: UUID = field(default_factory=uuid4)
    stages: list[Stage] = field(default_factory=list)
    prev_board: Board | None = field(compare=False, default=None)
    selected: int = 0

    def __post_init__(self) -> None:
        self.__fix_board_linking()

    def __fix_board_linking(self) -> None:
        for stage in self.stages:
            for task in stage:
                if task.next_board is not None:
                    task.next_board.prev_board = self
                    task.next_board.__fix_board_linking()

    @classmethod
    def default(
        cls,
        title: str,
        next_board: Board | None = None,
        *,
        # FIXME: Remove me later
        prefilled: bool = False,
    ) -> Self:
        def get_tasks(i: int) -> list[Task]:
            tasks: list[Task] = []
            for j, name in enumerate(random_tasks()):
                if i == 0 and j == 0:
                    tasks.append(Task(name=name, next_board=next_board))
                else:
                    tasks.append(Task(name=name))
            return tasks

        return cls(
            title,
            stages=[
                Stage(title, tasks=get_tasks(i) if prefilled else [])
                for i, title in enumerate(Board.DefaultStages)
            ],
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

        board = Board.default(title=task.name, prefilled=prefilled)
        board.prev_board = self
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

    def root_board(self) -> Board:
        while self.prev_board is not None:
            self = self.goto_prev_board()
        return self

    def find_board(self, id: UUID) -> Board:
        if self.id == id:
            return self
        for stage in self.stages:
            for task in stage:
                if task.next_board is not None:
                    # FIXME: improve this
                    with suppress(ValueError):
                        return task.next_board.find_board(id)
        raise ValueError(f"no board with {id=} found")

    def __iter__(self) -> Iterator[Stage]:
        return iter(self.stages)

    def __len__(self) -> int:
        return len(self.stages)

    @property
    def stage(self) -> Stage:
        return self.stages[self.selected]


@dataclass
class Task:
    name: str
    id: UUID = field(default_factory=uuid4)
    next_board: Board | None = None

    def __len__(self) -> int:
        return len(self.name)


@dataclass
class Stage:
    title: str
    id: UUID = field(default_factory=uuid4)
    tasks: list[Task] = field(default_factory=list)
    selected: int = 0

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

    def __iter__(self) -> Iterator[Task]:
        return iter(self.tasks)

    def __getitem__(self, idx: int) -> Task:
        if idx >= len(self.tasks):
            raise IndexError("stage index out of range")
        return self.tasks[idx]

    def __len__(self) -> int:
        return len(self.tasks)

    @property
    def task(self) -> Task:
        return self.tasks[self.selected]


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


def dump_board(board: Board, level: int = 0) -> None:
    print(f"{'    ' * level}Board: {board.title}")
    level_stage = level + 1
    level_task = level + 2
    for stage in board:
        print(f"{'    ' * level_stage}Stage: {stage.title}")
        level += 1
        for task in stage:
            print(f"{'    ' * level_task}Task: {task.name}")
            if task.next_board is not None:
                dump_board(task.next_board, level=level_task + 1)
