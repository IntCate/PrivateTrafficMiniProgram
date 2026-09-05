"""售后工单模块业务逻辑。对齐 docs/api-design.md §12 与 database-design §3.14。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.after_sale.models import (
    AFTER_SALE_APPLYING,
    AFTER_SALE_STATUS_TEXT,
    AfterSale,
)
from app.modules.after_sale.repository import AfterSaleRepository
from app.modules.after_sale.schemas import (
    AfterSaleItemOut,
    AfterSaleListOut,
    CreateAfterSaleRequest,
)
from app.modules.order.models import REFUNDABLE_STATUSES, Order


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _restore_stock(db: Session, order: Order) -> None:
    """售后回补库存：支付已实扣，退款恢复可售（对齐 PRD §4.x）。"""
    from app.modules.order.models import OrderItem
    from app.modules.product.models import ProductSku

    items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    for item in items:
        sku = db.get(ProductSku, item.sku_id)
        if sku:
            sku.stock += item.quantity


def _get_owned_after_sale(db: Session, user_id: int, after_sale_id: int) -> AfterSale:
    """加载本人售后单：不存在 404 / 越权 1403。"""
    row = db.get(AfterSale, after_sale_id)
    if row is None:
        raise BizException(404, "售后单不存在")
    if row.user_id != user_id:
        raise BizException(1403, "售后单归属不匹配")
    return row


def create_after_sale(
    db: Session, user_id: int, body: CreateAfterSaleRequest
) -> AfterSaleItemOut:
    """申请售后（对齐 api-design §12.1 / test-cases B5-14）。

    - 订单不存在/非本人 → 404/1403；
    - 订单状态非 paid/shipped/completed → 1402；
    - 同一订单已有 applying/approved 售后单 → 1606（重复申请）；
    - 申请金额默认取订单实付金额（服务端核算，不信任客户端）；
    - 申请成功即建工单，并把订单转为 `refund`（售后中）：回补已实扣库存、记录退款字段。
      统一售后入口为 `POST /api/after-sales`（旧 `POST /orders/{id}/refund` 已下线）。
    """
    order = db.get(Order, body.order_id)
    if order is None:
        raise BizException(404, "订单不存在")
    if order.user_id != user_id:
        raise BizException(1403, "订单归属不匹配")
    if order.status not in REFUNDABLE_STATUSES:
        raise BizException(1402, "订单状态不允许申请售后")

    existing = db.scalars(
        select(AfterSale).where(
            AfterSale.order_id == body.order_id,
            AfterSale.status.in_(["applying", "approved"]),
        )
    ).first()
    if existing is not None:
        raise BizException(1606, "该订单已有进行中的售后申请")

    amount = Decimal(str(body.amount)) if body.amount > 0 else order.pay_amount
    row = AfterSale(
        order_id=body.order_id,
        user_id=user_id,
        type=body.type,
        reason=body.reason,
        amount=amount,
        status=AFTER_SALE_APPLYING,
        images=body.images or None,
    )
    db.add(row)
    # 订单转售后中：回补库存 + 记录退款字段（与旧订单退款语义一致）
    original_status = order.status
    _restore_stock(db, order)
    order.status = "refund"
    order.refund_reason = body.reason or "不符合预期"
    order.refund_type = "refund" if original_status == "paid" else "return"
    order.refund_time = datetime.now()
    db.flush()
    db.commit()
    return _to_item(row)


def list_after_sales(
    db: Session, user_id: int, status: str | None, page: int, page_size: int
) -> AfterSaleListOut:
    """售后单列表（对齐 api-design §12.2）。"""
    rows, total = AfterSaleRepository(db).list_by_user(user_id, status, page, page_size)
    items = [_to_item(r) for r in rows]
    return AfterSaleListOut(
        items=items, total=total, page=page, page_size=page_size, has_more=page * page_size < total
    )


def get_after_sale(db: Session, user_id: int, after_sale_id: int) -> AfterSaleItemOut:
    """售后单详情（对齐 api-design §12.2）。"""
    return _to_item(_get_owned_after_sale(db, user_id, after_sale_id))


def _to_item(row: AfterSale) -> AfterSaleItemOut:
    return AfterSaleItemOut(
        id=row.id,
        order_id=row.order_id,
        type=row.type,
        reason=row.reason,
        amount=float(row.amount),
        status=row.status,
        status_text=AFTER_SALE_STATUS_TEXT.get(row.status, row.status),
        images=row.images or [],
        audit_remark=row.audit_remark,
        create_time=_fmt_dt(row.created_at),
    )
