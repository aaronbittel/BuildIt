import logging

from src.tui.board import Board, Stage, Task
from src.tui.event import (
    AddStage,
    AddTask,
    BoardEvent,
    EditStage,
    EditTask,
)
from src.tui.storage import Storage
from src.tui.ui import Id, UIContext


class App:
    def __init__(self, board: Board, storage: Storage) -> None:
        self.board = board
        self.storage = storage

        self.running = True

    def open_textfield(
        self,
        ctx: UIContext,
        event_type: BoardEvent,
        textfield_id: Id,
        initial_text: str = "",
    ) -> None:
        ctx.uistate.textfield_open = True
        ctx.uistate.textfield_str = initial_text
        ctx.board_event = event_type
        ctx.uistate.active_id = textfield_id

    # TODO: refactor isinstance checks
    def handle_accept_textfield(self, ctx: UIContext) -> None:
        assert ctx.board_event is not None

        if isinstance(ctx.board_event, AddTask):
            self.board.stage.add(Task(name=ctx.uistate.textfield_str))
        elif isinstance(ctx.board_event, EditTask):
            self.board.stage.task.name = ctx.uistate.textfield_str
        elif isinstance(ctx.board_event, AddStage):
            self.board.add_stage(Stage(title=ctx.uistate.textfield_str))
            self.board.selected = len(self.board.stages) - 1
        elif isinstance(ctx.board_event, EditStage):
            self.board.stage.title = ctx.uistate.textfield_str
        else:
            logging.error("open_textfield: unexpected event: %s", ctx.board_event)
            logging.error(f"type={type(ctx.board_event)}")
            assert False, "unreachable"

        ctx.board_event = None
        ctx.uistate.textfield_str = ""
        ctx.uistate.textfield_open = False
        ctx.uistate.active_id = None

    def handle_cancel_textfield(self, ctx: UIContext) -> None:
        ctx.uistate.textfield_str = ""
        ctx.uistate.textfield_open = False
        ctx.board_event = None
        ctx.uistate.active_id = None
