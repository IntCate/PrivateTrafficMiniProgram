"""积分模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from pydantic import Field

from app.common.schemas import CamelModel


class PointsLogItemOut(CamelModel):
    """积分明细项（对齐 api-design §11.4）。"""

    id: int
    change: int
    balance: int
    type: str
    biz_type: str
    remark: str | None = None
    created_at: str


class PointsLogListOut(CamelModel):
    """积分明细分页列表（对齐 api-design §11.4）。"""

    items: list[PointsLogItemOut] = Field(default_factory=list, serialization_alias="list")
    total: int
    page: int
    page_size: int
    has_more: bool
