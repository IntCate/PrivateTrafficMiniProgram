"""优惠券模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from pydantic import Field

from app.common.schemas import CamelModel


class CouponItemOut(CamelModel):
    """用户优惠券列表项（对齐 api-design §11.3）。"""

    id: int
    coupon_id: int
    name: str
    type: str
    amount: float | None = None
    discount: float | None = None
    min_amount: float = 0.0
    status: str
    valid_start: str | None = None
    valid_end: str | None = None


class CouponListOut(CamelModel):
    """用户优惠券分页列表（对齐 api-design §11.3）。"""

    items: list[CouponItemOut] = Field(default_factory=list, serialization_alias="list")
    total: int
    page: int
    page_size: int
    has_more: bool


class CouponActionOut(CamelModel):
    """领取优惠券结果。"""

    user_coupon_id: int
    existed: bool = False
