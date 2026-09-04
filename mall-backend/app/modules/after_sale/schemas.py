"""售后工单模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from pydantic import Field

from app.common.schemas import CamelModel, CamelRequest


class CreateAfterSaleRequest(CamelRequest):
    """申请售后（对齐 api-design §12.1）。"""

    order_id: int
    type: str = "refund"
    reason: str
    amount: float = 0.0
    images: list[str] = Field(default_factory=list)


class AfterSaleItemOut(CamelModel):
    """售后单列表项（对齐 api-design §12.2）。"""

    id: int
    order_id: int
    type: str
    reason: str
    amount: float
    status: str
    status_text: str
    images: list[str] = Field(default_factory=list)
    audit_remark: str | None = None
    create_time: str


class AfterSaleListOut(CamelModel):
    """售后单分页列表（对齐 api-design §12.2）。"""

    items: list[AfterSaleItemOut] = Field(default_factory=list, serialization_alias="list")
    total: int
    page: int
    page_size: int
    has_more: bool
