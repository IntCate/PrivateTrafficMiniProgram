"""优惠券模块路由。对齐 docs/api-design.md §11.3。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import get_current_member
from app.core.database import get_db
from app.core.response import ok
from app.modules.auth.models import Member
from app.modules.coupon.service import list_coupons, receive_coupon

router = APIRouter(prefix="/coupons", tags=["coupons"])


@router.get("")
def list_coupons_endpoint(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """用户优惠券列表 🔒（对齐 api-design §11.3）。"""
    return ok(list_coupons(db, member.id, status, page, page_size))


@router.post("/{coupon_id}/receive")
def receive_coupon_endpoint(
    coupon_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """领取优惠券 🔒（对齐 api-design §11.3）。"""
    return ok(receive_coupon(db, member.id, coupon_id))
