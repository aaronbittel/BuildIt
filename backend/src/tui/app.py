import logging

from src.tui.board import Board, Stage, Task
from src.tui.ui import EventType, Id, UIContext


class App:
    def __init__(self, board: Board) -> None:
        self.board = board

        self.running = True

    def open_textfield(
        self,
        ctx: UIContext,
        event_type: EventType,
        textfield_id: Id,
        initial_text: str = "",
    ) -> None:
        ctx.uistate.textfield_open = True
        ctx.uistate.textfield_str = initial_text
        ctx.event_type = event_type
        ctx.uistate.active_id = textfield_id

    def handle_accept_textfield(self, ctx: UIContext) -> None:
        assert ctx.event_type is not None

        if ctx.event_type == "Add Task":
            self.board.stage.add(Task(name=ctx.uistate.textfield_str))
        elif ctx.event_type == "Edit Task":
            self.board.stage.task.name = ctx.uistate.textfield_str
        elif ctx.event_type == "Add Stage":
            self.board.add_stage(Stage(title=ctx.uistate.textfield_str))
            self.board.selected = len(self.board.stages) - 1
        elif ctx.event_type == "Edit Stage":
            self.board.stage.title = ctx.uistate.textfield_str
        elif ctx.event_type == "Saving":
            pass
        else:
            logging.error("unexpected event: %s", ctx.event_type)
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
