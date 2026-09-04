"""积分模块 ORM 模型：积分明细。对齐 docs/database-design.md §3.12。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base

# 积分变动类型（对齐 database-design §3.12）
POINTS_TYPE_EARN = "earn"
POINTS_TYPE_CONSUME = "consume"
POINTS_TYPE_REFUND = "refund"

# 业务场景（对齐 database-design §3.12）
POINTS_BIZ_ORDER = "order"
POINTS_BIZ_PROMOTION = "promotion"
POINTS_BIZ_ADMIN = "admin"


class PointsLog(Base):
    """积分明细。"""

    __tablename__ = "points_log"
    __table_args__ = (Index("idx_user", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("member.id"), comment="会员 ID"
    )
    change: Mapped[int] = mapped_column(Integer, default=0, comment="变动值（正增负减）")
    balance: Mapped[int] = mapped_column(Integer, default=0, comment="变动后余额")
    type: Mapped[str] = mapped_column(
        String(20), comment="earn 获得 / consume 消费 / refund 退回"
    )
    biz_type: Mapped[str] = mapped_column(
        String(32), comment="业务场景：order/promotion/admin"
    )
    remark: Mapped[str | None] = mapped_column(String(255), comment="说明")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
