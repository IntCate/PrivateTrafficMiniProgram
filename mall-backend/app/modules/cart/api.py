"""购物车模块路由。对齐 docs/api-design.md §7。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps import get_current_member
from app.core.database import get_db
from app.core.response import ok
from app.modules.auth.models import Member
from app.modules.cart.schemas import (
    AddItemRequest,
    DeleteItemsRequest,
    SelectAllRequest,
    UpdateItemRequest,
)
from app.modules.cart.service import (
    add_item,
    delete_items,
    get_cart,
    select_all,
    update_item,
)

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("")
def get_cart_endpoint(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """购物车列表 🔒（对齐 api-design §7.1）。"""
    return ok(get_cart(db, member.id))


@router.post("/items")
def add_item_endpoint(
    body: AddItemRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """加入购物车 🔒（对齐 api-design §7.2）。"""
    return ok(
        add_item(db, member.id, body.sku_id, body.quantity, body.selected)
    )


@router.put("/items/{item_id}")
def update_item_endpoint(
    item_id: int,
    body: UpdateItemRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """修改购物车项 🔒（对齐 api-design §7.3）。"""
    return ok(
        update_item(
            db,
            member.id,
            item_id,
            body.quantity,
            body.selected,
            body.sku_id,
        )
    )


@router.delete("/items/{item_id}")
def delete_item_endpoint(
    item_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """删除单个购物车项 🔒（对齐 api-design §7.4）。"""
    return ok(delete_items(db, member.id, [item_id]))


@router.delete("/items")
def delete_items_endpoint(
    body: DeleteItemsRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """批量删除购物车项 🔒（对齐 api-design §7.5）。"""
    return ok(delete_items(db, member.id, body.ids))


@router.put("/select-all")
def select_all_endpoint(
    body: SelectAllRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """全选/取消全选 🔒（对齐 api-design §7.6）。"""
    return ok(select_all(db, member.id, body.selected))
