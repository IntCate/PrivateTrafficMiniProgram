"""收货地址 ORM 模型。对齐 database-design §3.6：含软删除列 + 双索引。"""
from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, BaseFields, SoftDeleteMixin

# 地址数量上限（对齐 error-code 1301 / api-design §8.2）
ADDRESS_MAX_COUNT = 20


class ShippingAddress(Base, BaseFields, SoftDeleteMixin):
    """收货地址。"""

    __tablename__ = "shipping_address"
    __table_args__ = (
        Index("idx_user_default", "user_id", "is_default"),
        Index("idx_user_deleted", "user_id", "deleted"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("member.id"), comment="会员 ID"
    )
    name: Mapped[str] = mapped_column(String(32), comment="收货人姓名")
    phone: Mapped[str] = mapped_column(String(20), comment="手机号")
    province: Mapped[str] = mapped_column(String(32), comment="省")
    city: Mapped[str] = mapped_column(String(32), comment="市")
    district: Mapped[str] = mapped_column(String(32), comment="区")
    detail: Mapped[str] = mapped_column(String(255), comment="详细地址")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否默认 1/0")
