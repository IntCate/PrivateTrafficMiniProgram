"""售后工单模块路由。对齐 docs/api-design.md §12。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import get_current_member
from app.core.database import get_db
from app.core.response import ok
from app.modules.after_sale.schemas import CreateAfterSaleRequest
from app.modules.after_sale.service import (
    create_after_sale,
    get_after_sale,
    list_after_sales,
)
from app.modules.auth.models import Member

router = APIRouter(prefix="/after-sales", tags=["after-sales"])


@router.post("")
def create_after_sale_endpoint(
    body: CreateAfterSaleRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """申请售后 🔒（对齐 api-design §12.1）。"""
    return ok(create_after_sale(db, member.id, body))


@router.get("")
def list_after_sales_endpoint(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """售后单列表 🔒（对齐 api-design §12.2）。"""
    return ok(list_after_sales(db, member.id, status, page, page_size))


@router.get("/{after_sale_id}")
def get_after_sale_endpoint(
    after_sale_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """售后单详情 🔒（对齐 api-design §12.2）。"""
    return ok(get_after_sale(db, member.id, after_sale_id))
