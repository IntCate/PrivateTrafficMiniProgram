"""优惠券模块 ORM 模型：券模板、用户券。对齐 docs/database-design.md §3.10/§3.11。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, BaseFields

# 券类型（对齐 database-design §3.10）
COUPON_TYPE_CASH = "cash"
COUPON_TYPE_DISCOUNT = "discount"
COUPON_TYPE_SHIPPING = "shipping"

# 用户券状态（对齐 database-design §3.11）
USER_COUPON_UNUSED = "unused"
USER_COUPON_USED = "used"
USER_COUPON_EXPIRED = "expired"


class Coupon(Base, BaseFields):
    """优惠券模板。"""

    __tablename__ = "coupon"

    name: Mapped[str] = mapped_column(String(64), comment="券名称")
    type: Mapped[str] = mapped_column(
        String(20), default=COUPON_TYPE_CASH, comment="cash 满减 / discount 折扣 / shipping 免运费"
    )
    amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="满减金额（cash 用）")
    discount: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), comment="折扣（discount 用，如 0.85）"
    )
    min_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="使用门槛"
    )
    total_count: Mapped[int] = mapped_column(Integer, default=0, comment="发放总量，0 不限")
    received_count: Mapped[int] = mapped_column(Integer, default=0, comment="已领取数量")
    valid_start: Mapped[datetime | None] = mapped_column(DateTime, comment="生效时间")
    valid_end: Mapped[datetime | None] = mapped_column(DateTime, comment="失效时间")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1 启用 / 0 停用")


class UserCoupon(Base, BaseFields):
    """用户优惠券领取记录。"""

    __tablename__ = "user_coupon"
    __table_args__ = (Index("idx_user_status", "user_id", "status"),)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("member.id"), comment="会员 ID")
    coupon_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("coupon.id"), comment="券模板 ID"
    )
    status: Mapped[str] = mapped_column(
        String(20), default=USER_COUPON_UNUSED, comment="unused/used/expired"
    )
    used_order_no: Mapped[str | None] = mapped_column(String(32), comment="核销订单号")
    used_at: Mapped[datetime | None] = mapped_column(DateTime, comment="使用时间")
