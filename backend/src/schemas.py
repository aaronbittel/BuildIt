from __future__ import annotations

import sqlite3
from dataclasses import field
from typing import Self

from pydantic import BaseModel as BaseSchema
from pydantic import Field


class StageCreate(BaseSchema):
    name: str


class StagePublic(StageCreate):
    id: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> StagePublic:
        return cls(**dict(row))


class TaskCreate(BaseSchema):
    name: str
    stage_id: int


class TaskPublic(TaskCreate):
    id: int
    position: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> TaskPublic:
        return cls(**dict(row))


class TaskNameUpdate(BaseSchema):
    name: str


class TaskMoveUpdate(BaseSchema):
    stage_id: int
    position: int = Field(alias="to_index")


class StageDetail(StagePublic):
    tasks: list[TaskPublic] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> StageDetail:
        return cls(**dict(row))

    def sort_by_position(self) -> Self:
        self.tasks.sort(key=lambda t: t.position)
        return self
