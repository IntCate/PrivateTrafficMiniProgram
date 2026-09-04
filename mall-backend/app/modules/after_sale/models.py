"""售后工单模块 ORM 模型。对齐 docs/database-design.md §3.14。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, BaseFields

# 售后类型（对齐 database-design §3.14）
AFTER_SALE_TYPE_REFUND = "refund"
AFTER_SALE_TYPE_RETURN = "return"

# 售后状态（对齐 database-design §3.14）
AFTER_SALE_APPLYING = "applying"
AFTER_SALE_APPROVED = "approved"
AFTER_SALE_REJECTED = "rejected"
AFTER_SALE_REFUNDED = "refunded"
AFTER_SALE_CLOSED = "closed"

# 状态文案
AFTER_SALE_STATUS_TEXT: dict[str, str] = {
    AFTER_SALE_APPLYING: "申请中",
    AFTER_SALE_APPROVED: "已通过",
    AFTER_SALE_REJECTED: "已驳回",
    AFTER_SALE_REFUNDED: "已退款",
    AFTER_SALE_CLOSED: "已关闭",
}


class AfterSale(Base, BaseFields):
    """售后工单。"""

    __tablename__ = "after_sale"
    __table_args__ = (
        Index("idx_order", "order_id"),
        Index("idx_user", "user_id", "status"),
    )

    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id"), comment="订单 ID"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("member.id"), comment="会员 ID"
    )
    type: Mapped[str] = mapped_column(
        String(20), comment="refund 仅退款 / return 退货退款"
    )
    reason: Mapped[str] = mapped_column(String(255), comment="申请原因")
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="申请金额"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=AFTER_SALE_APPLYING,
        comment="applying/approved/rejected/refunded/closed",
    )
    images: Mapped[list | None] = mapped_column(JSON, comment="凭证图片")
    audit_remark: Mapped[str | None] = mapped_column(String(255), comment="审核意见")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
