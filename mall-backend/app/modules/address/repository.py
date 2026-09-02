"""收货地址模块数据访问。"""
from __future__ import annotations

from sqlalchemy import select, update

from app.common.repository import BaseRepository
from app.modules.address.models import ShippingAddress


class AddressRepository(BaseRepository[ShippingAddress]):
    model = ShippingAddress

    def list_by_user(self, user_id: int) -> list[ShippingAddress]:
        """查询用户未删除地址：默认优先、创建时间倒序（对齐 api-design §8.1）。"""
        stmt = (
            select(ShippingAddress)
            .where(
                ShippingAddress.user_id == user_id,
                ShippingAddress.deleted == False,  # noqa: E712
            )
            .order_by(
                ShippingAddress.is_default.desc(),
                ShippingAddress.created_at.desc(),
                ShippingAddress.id.desc(),
            )
        )
        return list(self.db.scalars(stmt))

    def get_owned(self, user_id: int, address_id: int) -> ShippingAddress | None:
        """按归属查询未删除地址（防越权：必须是本人的地址）。"""
        stmt = select(ShippingAddress).where(
            ShippingAddress.id == address_id,
            ShippingAddress.user_id == user_id,
            ShippingAddress.deleted == False,  # noqa: E712
        )
        return self.db.scalar(stmt)

    def count_by_user(self, user_id: int) -> int:
        """未删除地址数量（对齐 api-design §8.2 上限校验）。"""
        stmt = select(ShippingAddress.id).where(
            ShippingAddress.user_id == user_id,
            ShippingAddress.deleted == False,  # noqa: E712
        )
        return len(list(self.db.scalars(stmt)))

    def clear_default(self, user_id: int) -> None:
        """将该用户全部地址默认标识置 0（同用户唯一默认）。"""
        self.db.execute(
            update(ShippingAddress)
            .where(ShippingAddress.user_id == user_id)
            .values(is_default=False)
        )

    def latest(self, user_id: int) -> ShippingAddress | None:
        """最新一条未删除地址（删除默认后转移默认用）。"""
        stmt = (
            select(ShippingAddress)
            .where(
                ShippingAddress.user_id == user_id,
                ShippingAddress.deleted == False,  # noqa: E712
            )
            .order_by(
                ShippingAddress.created_at.desc(),
                ShippingAddress.id.desc(),
            )
            .limit(1)
        )
        return self.db.scalar(stmt)
