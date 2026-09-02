"""购物车 ORM 模型。对齐 docs/database-design.md §3.5：无软删除列，uk_user_sku 唯一约束。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base

# 单次限购上限（对齐 api-design §7.2 / error-code 1201）
CART_QUANTITY_MAX = 99


class Cart(Base):
    """购物车项。"""

    __tablename__ = "cart"
    __table_args__ = (
        UniqueConstraint("user_id", "sku_id", name="uk_user_sku"),
        Index("idx_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("member.id"), comment="会员 ID"
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), comment="商品 ID"
    )
    sku_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product_sku.id"), comment="SKU ID"
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, comment="数量")
    selected: Mapped[bool] = mapped_column(Boolean, default=False, comment="勾选 1/0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
