"""统一响应与分页对象。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    """成功响应体。"""
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict[str, Any]:
    """失败响应体。"""
    return {"code": code, "message": message, "data": data}


class PageResult(BaseModel, Generic[T]):
    """统一分页对象。"""

    list: list[T]
    total: int
    page: int
    pageSize: int
    hasMore: bool
