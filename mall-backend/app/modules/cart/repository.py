"""购物车模块数据访问。"""
from __future__ import annotations

from typing import Any, cast

from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult

from app.common.repository import BaseRepository
from app.modules.cart.models import Cart


class CartRepository(BaseRepository[Cart]):
    model = Cart

    def list_by_user(self, user_id: int) -> list[Cart]:
        """查询用户全部购物车项（新添加在前）。"""
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .order_by(Cart.id.desc())
        )
        return list(self.db.scalars(stmt))

    def get_owned(self, user_id: int, item_id: int) -> Cart | None:
        """按归属查询单条购物车项（防越权：必须是本人的项）。"""
        stmt = select(Cart).where(Cart.id == item_id, Cart.user_id == user_id)
        return self.db.scalar(stmt)

    def get_by_user_sku(self, user_id: int, sku_id: int) -> Cart | None:
        """按用户+SKU 查询（uk_user_sku 唯一约束）。"""
        stmt = select(Cart).where(Cart.user_id == user_id, Cart.sku_id == sku_id)
        return self.db.scalar(stmt)

    def delete_owned(self, user_id: int, ids: list[int]) -> int:
        """物理删除用户拥有的购物车项，返回删除条数。"""
        stmt = delete(Cart).where(Cart.user_id == user_id, Cart.id.in_(ids))
        result = cast(CursorResult[Any], self.db.execute(stmt))
        return result.rowcount or 0

    def delete_by_skus(self, user_id: int, sku_ids: list[int]) -> int:
        """按 SKU 物理删除购物车项（下单结算后清理，对齐 api-design §9.2），返回删除条数。"""
        stmt = delete(Cart).where(Cart.user_id == user_id, Cart.sku_id.in_(sku_ids))
        result = cast(CursorResult[Any], self.db.execute(stmt))
        return result.rowcount or 0

    def set_all_selected(self, user_id: int, selected: bool) -> None:
        """全部购物车项勾选/取消。"""
        self.db.execute(
            update(Cart).where(Cart.user_id == user_id).values(selected=selected)
        )

    def set_select_where(self, user_id: int, ids: list[int], selected: bool) -> None:
        """对指定购物车项批量设置勾选。"""
        self.db.execute(
            update(Cart)
            .where(Cart.user_id == user_id, Cart.id.in_(ids))
            .values(selected=selected)
        )
