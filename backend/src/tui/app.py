import logging

from src.tui.board import Board, Stage, Task
from src.tui.event import AddStage, AddTask, BoardEvent, EditStage, EditTask
from src.tui.ui import Id, UIContext


class App:
    def __init__(self, board: Board) -> None:
        self.board = board

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
        ctx.event_type = event_type
        ctx.uistate.active_id = textfield_id

    # TODO: refactor isinstance checks
    def handle_accept_textfield(self, ctx: UIContext) -> None:
        assert ctx.event_type is not None

        if isinstance(ctx.event_type, AddTask):
            self.board.stage.add(Task(name=ctx.uistate.textfield_str))
        elif isinstance(ctx.event_type, EditTask):
            self.board.stage.task.name = ctx.uistate.textfield_str
        elif isinstance(ctx.event_type, AddStage):
            self.board.add_stage(Stage(title=ctx.uistate.textfield_str))
            self.board.selected = len(self.board.stages) - 1
        elif isinstance(ctx.event_type, EditStage):
            self.board.stage.title = ctx.uistate.textfield_str
        else:
            logging.error("open_textfield: unexpected event: %s", ctx.event_type)
            logging.error(f"type={type(ctx.event_type)}")
            assert False, "unreachable"

        ctx.event_type = None
        ctx.uistate.textfield_str = ""
        ctx.uistate.textfield_open = False
        ctx.uistate.active_id = None

    def handle_cancel_textfield(self, ctx: UIContext) -> None:
        ctx.uistate.textfield_str = ""
        ctx.uistate.textfield_open = False
        ctx.event_type = None
        ctx.uistate.active_id = None
