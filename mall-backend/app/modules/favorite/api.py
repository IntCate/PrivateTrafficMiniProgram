"""收藏模块路由。对齐 docs/api-design.md §10。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import get_current_member
from app.core.database import get_db
from app.core.response import ok
from app.modules.auth.models import Member
from app.modules.favorite.service import add_favorite, list_favorites, remove_favorite

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("")
def list_favorites_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """收藏列表 🔒（对齐 api-design §10.1）。"""
    return ok(list_favorites(db, member.id, page, page_size))


@router.post("/{product_id}")
def add_favorite_endpoint(
    product_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """添加收藏 🔒（对齐 api-design §10.2，幂等）。"""
    return ok(add_favorite(db, member.id, product_id))


@router.delete("/{product_id}")
def remove_favorite_endpoint(
    product_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """取消收藏 🔒（对齐 api-design §10.3，幂等）。"""
    return ok(remove_favorite(db, member.id, product_id))
