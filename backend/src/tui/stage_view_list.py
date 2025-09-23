import logging
from src.tui.stage_view import Stage, StageView


class StageViewList:
    def __init__(
        self,
        y: int,
        stages: list[Stage],
        space_perc: float,
        cols: int,
        min_width=20,
    ) -> None:
        assert len(stages) > 0

        self.y = y
        self.stages = stages
        self.cols = cols
        self.space_perc = space_perc
        self.min_width = min_width

        self.use_vertical_layout = False

        self.stage_views = [StageView(stage) for stage in stages]

        self._selected = 0
        self.selected.highlighted = True
        self._dirty_views: set[StageView] = set(self.stage_views)

        self.resize(cols)

    def draw(self) -> None:
        for view in self._dirty_views:
            view.draw()
        self._dirty_views.clear()

    def resize(self, cols: int) -> None:
        self.cols = cols

        space_len = int(self.cols * self.space_perc)
        content_width = self.cols - space_len * (len(self.stages) + 1)
        width_per_stageview = content_width // len(self.stages)

        self.use_vertical_layout = width_per_stageview < self.min_width

        for view in self.stage_views:
            view.clear()

        if self.use_vertical_layout:
            self._vertical_layout(cols)
        else:
            self._horizontal_layout(space_len, width_per_stageview)

        self._dirty_views = set(self.stage_views)

    def _vertical_layout(self, cols: int) -> None:
        y = self.y
        for view in self.stage_views:
            view.resize(y=y, x=0, width=cols)
            y += view.view_height

    def _horizontal_layout(self, space_len: int, width_per_stageview: int) -> None:
        for i, view in enumerate(self.stage_views):
            x = space_len + i * (width_per_stageview + space_len)
            view.resize(y=self.y, x=x, width=width_per_stageview)

    def selected_task(self) -> str:
        return self.selected.text

    def update_task(self, task: str) -> str:
        self._dirty_views.add(self.selected)
        return self.selected.update(task)

    def add_task(self, task: str) -> None:
        self._dirty_views.add(self.selected)
        self.selected.add(task)
        self.resize(self.cols)

    def remove_task(self) -> None:
        self._dirty_views.add(self.selected)
        self.selected.remove()
        self.resize(self.cols)

    # FIXME:
    def move_task_forward(self) -> None:
        task = self.selected.text
        # no task to move
        if task == "":
            return
        self.remove_task()
        next_stage = self._selected + 1
        next_stage = next_stage if next_stage < len(self.stage_views) else 0
        self.stage_views[next_stage].add(task)
        self._dirty_views.add(self.stage_views[next_stage])
        self.resize(self.cols)

    # FIXME:
    def move_task_back(self) -> None:
        task = self.selected.text
        # no task to move
        if task == "":
            return

        self.remove_task()
        next_stage = self._selected - 1
        next_stage = next_stage if next_stage >= 0 else len(self.stage_views) - 1
        self.stage_views[next_stage].add(task)
        self._dirty_views.add(self.stage_views[next_stage])
        self.resize(self.cols)

    def next_task(self) -> None:
        self._dirty_views.add(self.selected)
        self.selected.next()
        self._dirty_views.add(self.selected)

    def prev_task(self) -> None:
        self._dirty_views.add(self.selected)
        self.selected.prev()
        self._dirty_views.add(self.selected)

    def next_stage(self) -> None:
        self._dirty_views.add(self.selected)
        self.selected.highlighted = False
        self._selected += 1
        if self._selected >= len(self.stage_views):
            self._selected = 0
        self.selected.highlighted = True
        self._dirty_views.add(self.selected)

    @property
    def selected(self) -> StageView:
        return self.stage_views[self._selected]

    @property
    def bottom(self) -> int:
        if self.use_vertical_layout:
            return self.stage_views[-1].bottom
        return self.y + max(map(lambda view: view.view_height, self.stage_views))
