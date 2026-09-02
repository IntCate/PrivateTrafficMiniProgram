"""收藏模块 ORM 模型。对齐 docs/database-design.md §3.9。

favorite 为纯关系表（id/user_id/product_id/created_at），无软删除/更新时间列，
故仅继承 Base + 手动声明 id/created_at（对齐 schema.sql §3.9）。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class Favorite(Base):
    """商品收藏（user + product 唯一）。"""

    __tablename__ = "favorite"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uk_user_product"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("member.id"), comment="会员 ID"
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), comment="商品 ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
