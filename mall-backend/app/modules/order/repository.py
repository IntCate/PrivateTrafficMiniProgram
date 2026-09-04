"""订单模块数据访问。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.common.repository import BaseRepository
from app.modules.order.models import (
    ORDER_STATUS_PENDING,
    STATS_STATUSES,
    Order,
    OrderItem,
)


class OrderRepository(BaseRepository[Order]):
    model = Order

    def list_timeout_pending(self, before: datetime, limit: int = 200) -> list[Order]:
        """查询超时未支付订单：status=pending 且 created_at < before（按创建时间升序）。"""
        stmt = (
            select(Order)
            .where(Order.status == ORDER_STATUS_PENDING, Order.created_at < before)
            .order_by(Order.created_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def list_by_user(
        self,
        user_id: int,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Order], int]:
        """按用户分页查询订单（新订单在前）。"""
        base = select(Order).where(Order.user_id == user_id)
        count_stmt = select(func.count(Order.id)).where(Order.user_id == user_id)
        if status:
            base = base.where(Order.status == status)
            count_stmt = count_stmt.where(Order.status == status)

        total = self.db.scalar(count_stmt) or 0
        rows = list(
            self.db.scalars(
                base.order_by(Order.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return rows, total

    def get_owned(self, user_id: int, order_id: int) -> Order | None:
        """按归属查询订单（防越权：必须是本人的订单）。"""
        stmt = select(Order).where(Order.id == order_id, Order.user_id == user_id)
        return self.db.scalar(stmt)

    def stats_by_user(self, user_id: int) -> dict[str, int]:
        """订单状态角标：仅统计 pending/paid/shipped/refund（对齐 api-design §9.11）。"""
        stmt = (
            select(Order.status, func.count(Order.id))
            .where(Order.user_id == user_id, Order.status.in_(STATS_STATUSES))
            .group_by(Order.status)
        )
        counts: dict[str, int] = {
            status: count for status, count in self.db.execute(stmt)
        }
        return {status: counts.get(status, 0) for status in STATS_STATUSES}


class OrderItemRepository(BaseRepository[OrderItem]):
    model = OrderItem

    def list_by_order_ids(self, order_ids: list[int]) -> list[OrderItem]:
        """按订单 ID 批量加载明细。"""
        if not order_ids:
            return []
        stmt = (
            select(OrderItem)
            .where(OrderItem.order_id.in_(order_ids))
            .order_by(OrderItem.id.asc())
        )
        return list(self.db.scalars(stmt))
