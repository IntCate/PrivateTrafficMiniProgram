"""订单模块路由。对齐 docs/api-design.md §9。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import get_current_member
from app.core.database import get_db
from app.core.response import ok
from app.modules.auth.models import Member
from app.modules.order.schemas import (
    CancelOrderRequest,
    CreateDirectOrderRequest,
    CreateOrderRequest,
    PayOrderRequest,
    RefundOrderRequest,
)
from app.modules.order.service import (
    buy_again,
    cancel_order,
    confirm_order,
    create_direct_order,
    create_order,
    get_order_detail,
    list_orders,
    order_stats,
    pay_order,
    preview_direct_order,
    preview_order,
    refund_order,
    remind_order,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/preview")
def preview_endpoint(
    cart_item_ids: str | None = Query(default=None, alias="cartItemIds"),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """结算预览 🔒（对齐 api-design §9.1）。"""
    return ok(preview_order(db, member.id, cart_item_ids))


@router.get("/preview-direct")
def preview_direct_endpoint(
    sku_id: int = Query(alias="skuId"),
    quantity: int = Query(default=1),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """直购结算预览 🔒（对齐 api-design §9.1 直购口径）。"""
    return ok(preview_direct_order(db, member.id, sku_id, quantity))


@router.post("/direct")
def create_direct_endpoint(
    body: CreateDirectOrderRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """直购下单 🔒（对齐 api-design §9.1 直购口径 / test-cases B5-3b）。"""
    return ok(
        create_direct_order(db, member.id, body.address_id, body.sku_id, body.quantity)
    )


@router.post("")
def create_order_endpoint(
    body: CreateOrderRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """创建订单 🔒（对齐 api-design §9.2）。"""
    return ok(
        create_order(
            db,
            member.id,
            body.address_id,
            [{"sku_id": i.sku_id, "quantity": i.quantity} for i in body.items],
        )
    )


@router.get("/stats")
def stats_endpoint(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """订单状态角标 🔒（对齐 api-design §9.11）。"""
    return ok(order_stats(db, member.id))


@router.get("")
def list_orders_endpoint(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """订单列表 🔒（对齐 api-design §9.3）。"""
    return ok(list_orders(db, member.id, status, page, page_size))


@router.get("/{order_id}")
def detail_endpoint(
    order_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """订单详情 🔒（对齐 api-design §9.4）。"""
    return ok(get_order_detail(db, member.id, order_id))


@router.post("/{order_id}/pay")
def pay_endpoint(
    order_id: int,
    body: PayOrderRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """支付订单 🔒（对齐 api-design §9.5，mock 支付）。"""
    return ok(pay_order(db, member.id, order_id, body.pay_type))


@router.post("/{order_id}/cancel")
def cancel_endpoint(
    order_id: int,
    body: CancelOrderRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """取消订单 🔒（对齐 api-design §9.6）。"""
    return ok(cancel_order(db, member.id, order_id, body.reason))


@router.post("/{order_id}/refund")
def refund_endpoint(
    order_id: int,
    body: RefundOrderRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """申请售后/退款 🔒（对齐 api-design §9.7）。"""
    return ok(refund_order(db, member.id, order_id, body.reason, body.type))


@router.post("/{order_id}/remind")
def remind_endpoint(
    order_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """提醒发货 🔒（对齐 api-design §9.8）。"""
    return ok(remind_order(db, member.id, order_id))


@router.post("/{order_id}/confirm")
def confirm_endpoint(
    order_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """确认收货 🔒（对齐 api-design §9.9）。"""
    return ok(confirm_order(db, member.id, order_id))


@router.post("/{order_id}/buy-again")
def buy_again_endpoint(
    order_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """再次购买 🔒（对齐 api-design §9.10）。"""
    return ok(buy_again(db, member.id, order_id))
