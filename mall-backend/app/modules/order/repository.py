"""订单模块数据访问。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import exists, func, select

from app.common.repository import BaseRepository
from app.modules.order.models import (
    ORDER_STATUS_PENDING,
    ORDER_STATUS_REFUND,
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
                base.order_by(*self._order_criteria(status))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return rows, total

    def _order_criteria(self, status: str | None) -> list:
        """列表排序：默认新订单在前；售后 tab 让"售后中（申请中）"的单子排最前，再按新到旧。"""
        if status == ORDER_STATUS_REFUND:
            from app.modules.after_sale.models import AFTER_SALE_APPLYING, AfterSale

            applying = exists().where(
                AfterSale.order_id == Order.id,
                AfterSale.status == AFTER_SALE_APPLYING,
            )
            return [applying.desc(), Order.id.desc()]
        return [Order.id.desc()]

    def get_owned(self, user_id: int, order_id: int) -> Order | None:
        """按归属查询订单（防越权：必须是本人的订单）。"""
        stmt = select(Order).where(Order.id == order_id, Order.user_id == user_id)
        return self.db.scalar(stmt)

    def stats_by_user(self, user_id: int) -> dict[str, int]:
        """订单状态角标：仅统计 pending/paid/shipped/refund（对齐 api-design §9.11）。

        refund 角标只统计仍"售后中（申请中）"的售后单——后台已通过/驳回/退款完成
        的单子不再计入，避免"两个已通过 + 一个申请中"却显示 3 的误导。
        """
        from app.modules.after_sale.models import AFTER_SALE_APPLYING, AfterSale

        stmt = (
            select(Order.status, func.count(Order.id))
            .where(Order.user_id == user_id, Order.status.in_(STATS_STATUSES))
            .group_by(Order.status)
        )
        counts: dict[str, int] = {
            status: count for status, count in self.db.execute(stmt)
        }
        result = {status: counts.get(status, 0) for status in STATS_STATUSES}
        applying = (
            select(func.count(func.distinct(Order.id)))
            .join(AfterSale, AfterSale.order_id == Order.id)
            .where(
                Order.user_id == user_id,
                Order.status == ORDER_STATUS_REFUND,
                AfterSale.status == AFTER_SALE_APPLYING,
            )
        )
        result["refund"] = self.db.scalar(applying) or 0
        return result


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
