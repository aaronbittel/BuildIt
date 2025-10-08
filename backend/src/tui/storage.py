# TODO: Handle if filename already exists, currently silently overwrites
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from src.tui.board import Board, Stage, Task

DATA_PATH = Path("data")


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
    link: UUID | None = None


@dataclass
class __StageImm:
    title: str
    tasks: list[__TaskImm]


@dataclass
class __BoardImm:
    id: UUID
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
            title=title_match.group("title"),
            id=UUID(title_match.group("uuid")),
            stages=[],
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
                    assert task_match is not None
                    cur_stage.tasks.append(
                        __TaskImm(
                            name=task_match.group("name"),
                            link=UUID(task_match.group("uuid")),
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
