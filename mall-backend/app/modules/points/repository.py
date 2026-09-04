"""积分模块数据访问。"""
from __future__ import annotations

from sqlalchemy import func, select

from app.common.repository import BaseRepository
from app.modules.points.models import PointsLog


class PointsLogRepository(BaseRepository[PointsLog]):
    model = PointsLog

    def list_by_user(
        self, user_id: int, page: int, page_size: int
    ) -> tuple[list[PointsLog], int]:
        """按用户分页查询积分明细（新在前）。"""
        count_stmt = select(func.count(PointsLog.id)).where(PointsLog.user_id == user_id)
        total = self.db.scalar(count_stmt) or 0
        rows = list(
            self.db.scalars(
                select(PointsLog)
                .where(PointsLog.user_id == user_id)
                .order_by(PointsLog.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return rows, total
