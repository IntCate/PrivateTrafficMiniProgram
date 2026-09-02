"""通用仓储基类：get / get_by / page / save / update / delete。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """业务仓储继承即用，提供通用 CRUD。"""

    model: type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id: int) -> T | None:
        return self.db.get(self.model, id)

    def get_by(self, **kwargs: Any) -> T | None:
        stmt = select(self.model).filter_by(**kwargs)
        return self.db.scalar(stmt)

    def list_by(self, **kwargs: Any) -> list[T]:
        stmt = select(self.model).filter_by(**kwargs)
        return list(self.db.scalars(stmt))

    def page(self, page: int, pageSize: int, **filters: Any) -> tuple[list[T], int]:
        stmt = select(self.model).filter_by(**filters)
        count_stmt = select(self.model).filter_by(**filters).with_only_columns(self.model.id)
        total = self.db.scalar(count_stmt) or 0
        rows = list(self.db.scalars(stmt.offset((page - 1) * pageSize).limit(pageSize)))
        return rows, total

    def save(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, obj: T) -> None:
        self.db.delete(obj)
        self.db.flush()
