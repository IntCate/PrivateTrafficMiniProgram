"""积分模块业务逻辑。对齐 docs/api-design.md §11.4 与 database-design §3.12。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.points.repository import PointsLogRepository
from app.modules.points.schemas import PointsLogItemOut, PointsLogListOut


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def list_points_logs(
    db: Session, user_id: int, page: int, page_size: int
) -> PointsLogListOut:
    """积分明细列表（对齐 api-design §11.4）。"""
    rows, total = PointsLogRepository(db).list_by_user(user_id, page, page_size)
    items = [
        PointsLogItemOut(
            id=r.id,
            change=r.change,
            balance=r.balance,
            type=r.type,
            biz_type=r.biz_type,
            remark=r.remark,
            created_at=_fmt_dt(r.created_at),
        )
        for r in rows
    ]
    return PointsLogListOut(
        items=items, total=total, page=page, page_size=page_size, has_more=page * page_size < total
    )
