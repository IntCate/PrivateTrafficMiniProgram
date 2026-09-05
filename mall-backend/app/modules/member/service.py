"""会员中心业务逻辑。对齐 docs/api-design.md §11 与 mock store.js。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.auth.models import Member
from app.modules.coupon.repository import UserCouponRepository
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
    """我的页聚合：会员信息 + 订单状态角标（对齐 api-design §11.1）。"""
    counts: dict[str, int] = OrderRepository(db).stats_by_user(member.id)
    return MemberOverviewOut(
        member=_member_out(db, member),
        order_stats=OrderStatsOut(**counts),
    )


def update_profile(
    db: Session, member: Member, req: UpdateProfileRequest
) -> ProfileOut:
    """更新本人昵称/头像（对齐 api-design §11.2，仅可更新本人）。

    - 昵称 1-20 字，非法 1003（对齐 mock「昵称长度需为 1-20 字」）
    - 头像必须为自有上传域的相对路径（`/uploads/` 开头，对齐 known-issues #9 白名单）：
      仅接受本平台上传的图片，外域 http(s) 链接一律拒绝，非法 1003
    """
    if not (NICKNAME_MIN <= len(req.nickname) <= NICKNAME_MAX):
        raise BizException(1003, "昵称长度需为 1-20 字")
    if req.avatar and not req.avatar.startswith("/uploads/"):
        raise BizException(1003, "头像必须为本平台上传的图片")

    member.nickname = req.nickname
    if req.avatar:
        member.avatar = req.avatar
    db.commit()
    return ProfileOut(nickname=member.nickname or "", avatar=member.avatar or "")


def _member_out(db: Session, member: Member) -> MemberOut:
    return MemberOut(
        id=member.id,
        nickname=member.nickname or "",
        avatar=member.avatar or "",
        member_level=member.member_level,
        member_level_text=MEMBER_LEVEL_TEXT.get(member.member_level, ""),
        points=member.points or 0,
        coupon_count=UserCouponRepository(db).count_unused(member.id),
    )
