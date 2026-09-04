"""售后工单模块数据访问。"""
from __future__ import annotations

from sqlalchemy import func, select

from app.common.repository import BaseRepository
from app.modules.after_sale.models import AfterSale


class AfterSaleRepository(BaseRepository[AfterSale]):
    model = AfterSale

    def list_by_user(
        self, user_id: int, status: str | None, page: int, page_size: int
    ) -> tuple[list[AfterSale], int]:
        """按用户分页查询售后单（新在前）。"""
        cond = [AfterSale.user_id == user_id]
        if status:
            cond.append(AfterSale.status == status)
        count_stmt = select(func.count(AfterSale.id)).where(*cond)
        total = self.db.scalar(count_stmt) or 0
        rows = list(
            self.db.scalars(
                select(AfterSale)
                .where(*cond)
                .order_by(AfterSale.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return rows, total
