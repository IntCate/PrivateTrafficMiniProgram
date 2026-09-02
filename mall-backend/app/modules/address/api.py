"""收货地址模块路由。对齐 docs/api-design.md §8。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps import get_current_member
from app.core.database import get_db
from app.core.response import ok
from app.modules.address.schemas import AddressRequest
from app.modules.address.service import (
    create_address,
    delete_address,
    list_addresses,
    set_default,
    update_address,
)
from app.modules.auth.models import Member

router = APIRouter(prefix="/addresses", tags=["address"])


@router.get("")
def list_endpoint(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """地址列表 🔒（对齐 api-design §8.1）。"""
    return ok(list_addresses(db, member.id))


@router.post("")
def create_endpoint(
    body: AddressRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """新增地址 🔒（对齐 api-design §8.2）。"""
    return ok(create_address(db, member.id, body))


@router.put("/{address_id}")
def update_endpoint(
    address_id: int,
    body: AddressRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """编辑地址 🔒（对齐 api-design §8.3）。"""
    return ok(update_address(db, member.id, address_id, body))


@router.delete("/{address_id}")
def delete_endpoint(
    address_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """删除地址 🔒（对齐 api-design §8.4）。"""
    return ok(delete_address(db, member.id, address_id))


@router.put("/{address_id}/default")
def set_default_endpoint(
    address_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """设为默认 🔒（对齐 api-design §8.5）。"""
    return ok(set_default(db, member.id, address_id))
