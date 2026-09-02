"""会员中心业务逻辑。对齐 docs/api-design.md §11 与 mock store.js。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.auth.models import Member
from app.modules.member.schemas import (
    MemberOut,
    MemberOverviewOut,
    ProfileOut,
    UpdateProfileRequest,
)
from app.modules.order.repository import OrderRepository
from app.modules.order.schemas import OrderStatsOut

# 会员等级文案（对齐 docs/database-design.md §3.1 等级字典）
MEMBER_LEVEL_TEXT = {
    "bronze": "普通会员",
    "silver": "白银会员",
    "gold": "黄金会员",
    "platinum": "铂金会员",
}

NICKNAME_MIN = 1
NICKNAME_MAX = 20


def get_overview(db: Session, member: Member) -> MemberOverviewOut:
    """我的页聚合：会员信息 + 订单状态角标（对齐 api-design §11.1）。

    couponCount：优惠券模块未上线（预留），恒为 0。
    """
    counts: dict[str, int] = OrderRepository(db).stats_by_user(member.id)
    return MemberOverviewOut(
        member=_member_out(member),
        order_stats=OrderStatsOut(**counts),
    )


def update_profile(
    db: Session, member: Member, req: UpdateProfileRequest
) -> ProfileOut:
    """更新本人昵称/头像（对齐 api-design §11.2，仅可更新本人）。

    - 昵称 1-20 字，非法 1003（对齐 mock「昵称长度需为 1-20 字」）
    - 头像 P0 校验 http(s) URL（对齐 mock「头像必须为有效的 URL」）；
      自有存储域收紧随上传接口上线后处理（见 docs/known-issues.md）
    """
    if not (NICKNAME_MIN <= len(req.nickname) <= NICKNAME_MAX):
        raise BizException(1003, "昵称长度需为 1-20 字")
    if req.avatar and not _is_http_url(req.avatar):
        raise BizException(1003, "头像必须为有效的 URL")

    member.nickname = req.nickname
    if req.avatar:
        member.avatar = req.avatar
    db.commit()
    return ProfileOut(nickname=member.nickname or "", avatar=member.avatar or "")


def _member_out(member: Member) -> MemberOut:
    return MemberOut(
        id=member.id,
        nickname=member.nickname or "",
        avatar=member.avatar or "",
        member_level=member.member_level,
        member_level_text=MEMBER_LEVEL_TEXT.get(member.member_level, ""),
        points=member.points or 0,
        coupon_count=0,
    )


def _is_http_url(url: str) -> bool:
    return url.lower().startswith(("http://", "https://"))
