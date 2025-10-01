from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Self


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
        self.selected = max(0, self.selected - 1)
        return task

    def next_task(self) -> None:
        if self.selected + 1 < len(self.tasks):
            self.selected += 1

    def prev_task(self) -> None:
        if self.selected - 1 >= 0:
            self.selected -= 1

    def move_task(self, dir: int) -> None:
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


class Board:
    DefaultStages = ["Backlog", "In Progress", "Done"]

    def __init__(
        self,
        title: str,
        stages: list[Stage] | None = None,
        prev_board: Board | None = None,
    ) -> None:
        self.title = title
        self.stages = stages if stages is not None else []
        self.prev_board = prev_board

        self.selected = 0

    @classmethod
    def default(
        cls,
        title: str,
        prev_board: Board | None = None,
    ) -> Self:
        return cls(
            title,
            stages=[
                Stage(t, tasks=[Task(name) for name in random_tasks()])
                for t in Board.DefaultStages
            ],
            prev_board=prev_board,
        )

    def goto_next_board(self, stage_idx: int, task_idx: int) -> Board:
        task = self.stages[stage_idx].tasks[task_idx]
        if task.next_board is not None:
            return task.next_board

        board = Board.default(title=task.name, prev_board=self)
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


if __name__ == "__main__":
    selected_stage = 0
    selected_task = 0

    stages = [
        Stage("Backlog", tasks=[Task("Todo 1"), Task("Todo 2"), Task("Todo 3")]),
        Stage("In Progress", tasks=[Task("Task 1"), Task("Task 2"), Task("Task 3")]),
        Stage("Done", tasks=[Task("Done 1"), Task("Done 2"), Task("Done 3")]),
    ]
    board = Board(title="Main Board", stages=stages)

    print(board)

    board = board.goto_next_board(0, 0)
    print(board)
    board.stages[selected_stage].add(Task(name="My New Todo"))
    selected_stage += 1
    board.stages[selected_stage].add(Task(name="My New Task"))
    board.stages[selected_stage].add(Task(name="My New Task"))
    print(board)

    board = board.goto_prev_board()
    print(board)

    board = board.goto_next_board(0, 0)
    print(board)
