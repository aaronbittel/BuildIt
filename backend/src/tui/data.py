from __future__ import annotations

import curses
import random
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self

from src.tui.layout import Layout

type Id = int


def widget_id(label: str, instance: int = 0) -> Id:
    import hashlib

    unique_str = f"{label}:{instance}"
    return int(hashlib.sha1(unique_str.encode()).hexdigest(), 16)


class UiState:
    def __init__(self) -> None:
        self.active_id: Id | None = None
        self.key: int = -1
        self.key_consumed = False


type BoardResult = Literal[
    "Add Task",
    "Edit Task",
    "Add Stage",
    "Edit Stage",
    "Saving",
]
type TextfieldResult = Literal["Continue", "Cancelled", "Accepted"]

type EventType = BoardResult | TextfieldResult
type Event = EventType | tuple[BoardResult, dict[str, str]]


@dataclass
class UIContext:
    stdscr: curses.window
    uistate: UiState
    layout: Layout | None = None
    event_type: BoardResult | None = None


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
        id: uuid.uuid1 | None = None,
    ) -> None:
        self.id = id if id is not None else uuid.uuid1()
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


DATA_PATH = Path("data")


# TODO: Handle if filename already exists, currently silently overwrites
def dump_state(board: Board, filename: str) -> None:
    def dump_board(dirname: Path, b: Board) -> None:
        name = f"root_{str(b.id)}" if b.prev_board is None else str(b.id)
        filename = dirname / name
        with filename.open(mode="w") as f:
            f.write(f"Title: {b.title} #{b.id}\n")
            f.write("Stages:\n")
            for stage in b.stages:
                f.write(f"\tTitle: {stage.title}\n")
                for task in stage.tasks:
                    next_board_link = (
                        f"#{task.next_board.id}" if task.next_board is not None else ""
                    )
                    f.write(f"\t\tName: {task.name} {next_board_link}\n")

    def bfs(dirname: Path, b: Board) -> None:
        dump_board(dirname, b)
        for stage in b.stages:
            for task in stage:
                if task.next_board is not None:
                    bfs(dirname, task.next_board)

    dirname = DATA_PATH / filename
    dirname.mkdir(exist_ok=True)

    root = board
    while root.prev_board is not None:
        root = root.prev_board

    bfs(dirname, root)


@dataclass
class __TaskImm:
    name: str
    link: uuid.UUID | None = None


@dataclass
class __StageImm:
    title: str
    tasks: list[__TaskImm]


@dataclass
class __BoardImm:
    id: uuid.UUID
    title: str
    stages: list[__StageImm]


def __load_state_imm(filename: str) -> list[__BoardImm]:
    import re

    title_uuid_pattern = re.compile(
        r"^Title:\s*(?P<title>.+?)\s+#(?P<uuid>[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F]{4}-1[0-9a-fA-F]{3}-"
        r"[89abAB][0-9a-fA-F]{3}-"
        r"[0-9a-fA-F]{12})$"
    )

    # fmt: off
    name_uuid_pattern = re.compile(
        r"^\s*Name:\s*(?P<name>.+?)"        # capture the name
        r"(?:\s+#(?P<uuid>[0-9a-fA-F]{8}-"  # non-capturing group for optional UUID
        r"[0-9a-fA-F]{4}-1[0-9a-fA-F]{3}-"
        r"[89abAB][0-9a-fA-F]{3}-"
        r"[0-9a-fA-F]{12}))?$"              # make it optional with ?
    )
    # fmt: on

    def parse_file(filepath: Path) -> __BoardImm:
        lines = [
            line.strip() for line in filepath.read_text().splitlines() if line.strip()
        ]

        title_match = title_uuid_pattern.match(lines[0])
        assert title_match is not None
        board = __BoardImm(
            title=title_match.group("title"), id=title_match.group("uuid"), stages=[]
        )
        assert lines[1] == "Stages:"

        i = 2
        t_prefix = "Title: "
        cur_stage = __StageImm(title="", tasks=[])

        while i < len(lines):
            if lines[i].startswith(t_prefix):
                cur_stage.title = lines[i][len(t_prefix) :]
                i += 1
                while i < len(lines) and lines[i].startswith("Name: "):
                    task_match = name_uuid_pattern.match(lines[i])
                    cur_stage.tasks.append(
                        __TaskImm(
                            name=task_match.group("name"), link=task_match.group("uuid")
                        )
                    )
                    i += 1
                board.stages.append(cur_stage)
            cur_stage = __StageImm(title="", tasks=[])

        return board

    basepath = DATA_PATH / filename
    return [parse_file(f) for f in basepath.iterdir()]


def convert_imm_boards_to_boards(imm_boards: list[__BoardImm]) -> Board:
    def goto(imm_board: __BoardImm):
        stages = []
        for imm_stage in imm_board.stages:
            tasks = []
            for imm_task in imm_stage.tasks:
                if imm_task.link is None:
                    tasks.append(Task(name=imm_task.name))
                    continue
                linked_board = next(filter(lambda b: b.id == imm_task.link, imm_boards))
                tasks.append(Task(name=imm_task.name, next_board=goto(linked_board)))
            stages.append(Stage(title=imm_stage.title, tasks=tasks))
        return Board(title=imm_board.title, id=imm_board.id, stages=stages)

    assert len(imm_boards) > 0
    root = imm_boards[0]

    return goto(root)


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
