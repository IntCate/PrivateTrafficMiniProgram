"""积分模块路由。对齐 docs/api-design.md §11.4。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import get_current_member
from app.core.database import get_db
from app.core.response import ok
from app.modules.auth.models import Member
from app.modules.points.service import list_points_logs

router = APIRouter(prefix="/points-logs", tags=["points"])


@router.get("")
def list_points_logs_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """积分明细列表 🔒（对齐 api-design §11.4）。"""
    return ok(list_points_logs(db, member.id, page, page_size))
