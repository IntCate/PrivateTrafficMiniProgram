"""会员中心 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from pydantic import Field, field_validator

from app.common.schemas import CamelModel, CamelRequest
from app.modules.order.schemas import OrderStatsOut


class MemberOut(CamelModel):
    """会员信息（对齐 api-design §11.1 member）。"""

    id: int
    nickname: str = ""
    avatar: str | None = None
    member_level: str
    member_level_text: str
    points: int = 0
    coupon_count: int = 0


class MemberOverviewOut(CamelModel):
    """我的页聚合数据（对齐 api-design §11.1）。"""

    member: MemberOut
    order_stats: OrderStatsOut


class UpdateProfileRequest(CamelRequest):
    """资料更新（对齐 api-design §11.2）。"""

    nickname: str
    avatar: str | None = None

    @field_validator("nickname")
    @classmethod
    def _trim_nickname(cls, v: str) -> str:
        return v.strip()


class ProfileOut(CamelModel):
    """资料更新结果（对齐 api-design §11.2）。"""

    nickname: str
    avatar: str | None = Field(default=None)
