from __future__ import annotations

from dataclasses import field
import sqlite3

from pydantic import BaseModel as BaseSchema, Field


# def update_model(cls: type[BaseSchema]):
#     """
#     Decorator that generates an Update version of a Pydantic model
#     with all fields optional and attaches it as `Update` on the class.
#     """
#     annotations = {k: Optional[v] for k, v in cls.__annotations__.items()}
#     update_cls = type(f"{cls.__name__}Update", (BaseSchema,), annotations)
#
#     # attach the generated class to the original for easy access
#     cls.Update = update_cls
#     return cls


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


class TaskUpdate(BaseSchema):
    name: str | None = None
    stage_id: int | None = None
    position: int = Field(alias="to_index")


class StageDetail(StagePublic):
    tasks: list[TaskPublic] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> StageDetail:
        return cls(**dict(row))
