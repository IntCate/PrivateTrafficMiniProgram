"""订单模块业务逻辑：结算预览/下单/列表/详情/支付/取消/售后/提醒/收货/再次购买/角标。

对齐 docs/api-design.md §9 与 docs/test-cases.md B5（行为与前端 mock store.js 一致）。
金额一律 Decimal 计算，输出转 float；库存口径 = stock - lock_stock。
"""
from __future__ import annotations

import logging
import random
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.address.models import ShippingAddress
from app.modules.auth.models import Member
from app.modules.cart.repository import CartRepository
from app.modules.order.models import (
    REFUNDABLE_STATUSES,
    STATUS_DESC,
    STATUS_TEXT,
    Order,
    OrderItem,
)
from app.modules.order.repository import OrderItemRepository, OrderRepository
from app.modules.order.schemas import (
    OrderListItemOut,
    OrderListOut,
    OrderStatsOut,
    PreviewAddressOut,
    PreviewItemOut,
    PreviewOut,
    ReceiverOut,
    UnavailableItem,
)
from app.modules.product.models import Product, ProductSku

logger = logging.getLogger("app.modules.order.service")

# 单次限购上限（对齐 error-code 1201）
ORDER_QUANTITY_MAX = 99

_DT_FMT = "%Y-%m-%d %H:%M:%S"


def _fmt_dt(dt: datetime | None) -> str | None:
    """datetime → "YYYY-MM-DD HH:MM:SS"（对齐 mock nowText 口径）。"""
    return dt.strftime(_DT_FMT) if dt else None


def _available_stock(sku: ProductSku) -> int:
    """可用库存 = 总库存 - 锁定库存。"""
    return max(sku.stock - sku.lock_stock, 0)


def _validate_quantity(quantity: int, available: int) -> int:
    """数量校验（对齐 api-design §9.1 / test-cases B5-3）。
    - 数量 < 1 → 400；超限购 → 1201；超库存 → 1104（data.availableStock）
    """
    if quantity < 1:
        raise BizException(400, "数量不能小于 1")
    if quantity > ORDER_QUANTITY_MAX:
        raise BizException(
            1201,
            f"单次限购 {ORDER_QUANTITY_MAX} 件",
            {"maxQuantity": ORDER_QUANTITY_MAX},
        )
    if quantity > available:
        raise BizException(1104, "库存不足", {"availableStock": available})
    return quantity


def _get_saleable_sku(db: Session, sku_id: int) -> tuple[Product, ProductSku]:
    """加载 SKU 与其商品，校验存在性与可售性（不存在 404 / 下架 1102）。"""
    sku = db.get(ProductSku, sku_id)
    if sku is None or sku.deleted:
        raise BizException(404, "SKU 不存在")
    product = db.get(Product, sku.product_id)
    if product is None or product.deleted:
        raise BizException(404, "商品不存在")
    if product.status != 1 or sku.status != 1:
        raise BizException(1102, "商品已下架")
    return product, sku


def _calc_amounts(product_items: list[dict]) -> dict[str, Decimal]:
    """金额计算：商品总额 + 免邮（P0 统一包邮，对齐 mock calcOrderAmounts）。"""
    total = sum((Decimal(str(p["price"])) * p["quantity"] for p in product_items), Decimal("0.00"))
    return {
        "totalAmount": total,
        "freight": Decimal("0.00"),
        "payAmount": total,
    }


def _gen_order_no(now: datetime) -> str:
    """订单号：K + yyyyMMddHHmmss + 3 位随机（对齐 mock generateOrderNo / schema §3.7）。"""
    ts = now.strftime("%Y%m%d%H%M%S")
    return f"K{ts}{random.randint(100, 999)}"


def _get_address(db: Session, user_id: int, address_id: int) -> ShippingAddress:
    """加载本人地址（防越权），不存在 404。"""
    stmt = select(ShippingAddress).where(
        ShippingAddress.id == address_id,
        ShippingAddress.user_id == user_id,
        ShippingAddress.deleted.is_(False),
    )
    address = db.scalar(stmt)
    if address is None:
        raise BizException(404, "地址不存在")
    return address


def _get_default_address(db: Session, user_id: int) -> ShippingAddress | None:
    """获取默认地址（无默认则取最新一条；对齐 mock buyAgain 取 defaultAddress）。"""
    stmt = (
        select(ShippingAddress)
        .where(ShippingAddress.user_id == user_id, ShippingAddress.deleted.is_(False))
        .order_by(ShippingAddress.is_default.desc(), ShippingAddress.id.desc())
    )
    return db.scalar(stmt)


def _list_addresses_for_preview(db: Session, user_id: int) -> list[dict]:
    """结算预览地址列表：默认优先、创建时间倒序（对齐 §9.1）。"""
    stmt = (
        select(ShippingAddress)
        .where(ShippingAddress.user_id == user_id, ShippingAddress.deleted.is_(False))
        .order_by(ShippingAddress.is_default.desc(), ShippingAddress.id.desc())
    )
    return [
        PreviewAddressOut(
            id=a.id,
            name=a.name,
            phone=a.phone,
            region_text=f"{a.province} {a.city} {a.district}",
            detail=a.detail,
            is_default=a.is_default,
        ).model_dump(by_alias=True)
        for a in db.scalars(stmt)
    ]


def _preoccupy_stock(db: Session, product_items: list[dict]) -> None:
    """预占库存：lock_stock += qty。"""
    for p in product_items:
        sku = db.get(ProductSku, p["sku_id"])
        if sku:
            sku.lock_stock += p["quantity"]


def _release_stock(db: Session, order: Order) -> None:
    """释放锁定库存：lock_stock -= qty（取消/售后时回补，对齐 mock releaseStock）。"""
    items = OrderItemRepository(db).list_by_order_ids([order.id])
    for item in items:
        sku = db.get(ProductSku, item.sku_id)
        if sku:
            sku.lock_stock = max(sku.lock_stock - item.quantity, 0)


def _build_order(
    db: Session,
    user_id: int,
    address: ShippingAddress,
    product_items: list[dict],
) -> Order:
    """创建订单主表 + 明细（快照），挂载到 Session（由调用方 commit）。"""
    amounts = _calc_amounts(product_items)
    order = Order(
        order_no=_gen_order_no(datetime.now()),
        user_id=user_id,
        status="pending",
        total_amount=amounts["totalAmount"],
        freight=amounts["freight"],
        pay_amount=amounts["payAmount"],
        receiver_name=address.name,
        receiver_phone=address.phone,
        receiver_region=f"{address.province} {address.city} {address.district}",
        receiver_detail=address.detail,
    )
    db.add(order)
    db.flush()
    for p in product_items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=p["product_id"],
                sku_id=p["sku_id"],
                product_name=p["name"],
                sku_text=p["sku_text"],
                image=p["image"],
                price=Decimal(str(p["price"])),
                quantity=p["quantity"],
            )
        )
    db.flush()
    return order


def _compute_actions(status: str) -> list[str]:
    """按状态计算可用动作（对齐 api-design §9.3 / mock computeActions）。"""
    return {
        "pending": ["pay", "cancel", "buyAgain"],
        "paid": ["remind", "refund", "buyAgain"],
        "shipped": ["confirm", "refund", "buyAgain"],
        "completed": ["refund", "buyAgain"],
        "cancelled": ["buyAgain"],
        "refund": ["buyAgain"],
    }.get(status, [])


def _receiver_dto(order: Order) -> dict:
    return ReceiverOut(
        name=order.receiver_name,
        phone=order.receiver_phone,
        region_text=order.receiver_region,
        detail=order.receiver_detail,
    ).model_dump(by_alias=True)


def _order_item_dtos(items: list[OrderItem]) -> list[dict]:
    return [
        {
            "id": i.id,
            "productName": i.product_name,
            "skuText": i.sku_text,
            "price": float(i.price),
            "quantity": i.quantity,
            "image": i.image,
        }
        for i in items
    ]


def _list_item_dto(order: Order, items: list[OrderItem]) -> dict:
    return OrderListItemOut(
        id=order.id,
        order_no=order.order_no,
        status=order.status,
        status_text=STATUS_TEXT.get(order.status, order.status),
        total_amount=float(order.total_amount),
        freight=float(order.freight),
        pay_amount=float(order.pay_amount),
        receiver=_receiver_dto(order),
        items=_order_item_dtos(items),
        create_time=_fmt_dt(order.created_at) or "",
        available_actions=_compute_actions(order.status),
    ).model_dump(by_alias=True)


def _detail_dto(order: Order, items: list[OrderItem]) -> dict:
    dto = _list_item_dto(order, items)
    dto["statusDesc"] = STATUS_DESC.get(order.status, "")
    dto["payType"] = order.pay_type
    dto["payTime"] = _fmt_dt(order.pay_time)
    dto["shipTime"] = _fmt_dt(order.ship_time)
    dto["finishTime"] = _fmt_dt(order.finish_time)
    return dto


def _load_items(db: Session, orders: list[Order]) -> dict[int, list[OrderItem]]:
    """按订单批量加载明细（dict[order_id, items]）。"""
    grouped: dict[int, list[OrderItem]] = {}
    for item in OrderItemRepository(db).list_by_order_ids([o.id for o in orders]):
        grouped.setdefault(item.order_id, []).append(item)
    return grouped


def _order_items(db: Session, order: Order) -> list[OrderItem]:
    """加载单个订单的明细。"""
    return OrderItemRepository(db).list_by_order_ids([order.id])


def _remove_cart_items(db: Session, user_id: int, sku_ids: list[int]) -> None:
    """下单后删除购物车中本次结算项（对齐 api-design §9.2 / mock createOrder）。"""
    if not sku_ids:
        return
    CartRepository(db).delete_by_skus(user_id, sku_ids)


def preview_order(db: Session, user_id: int, cart_item_ids: str | None = None) -> dict:
    """结算预览（对齐 api-design §9.1 / test-cases B5-1/B5-2/B5-3）。
    - 不传 cartItemIds 默认取全部勾选项；为空 → 400
    - 含不可售项 → 1203（data.unavailables）；数量超库存 → 1104
    """
    items = CartRepository(db).list_by_user(user_id)
    if cart_item_ids:
        id_set = {int(x) for x in cart_item_ids.split(",")}
        selected = [i for i in items if i.id in id_set]
    else:
        selected = [i for i in items if i.selected]
    if not selected:
        raise BizException(400, "请先选择要结算的商品")

    unavailables: list[dict] = []
    preview_items: list[dict] = []
    for item in selected:
        sku = db.get(ProductSku, item.sku_id)
        product = db.get(Product, item.product_id) if sku else None
        unavailable = (
            sku is None
            or sku.deleted
            or product is None
            or product.deleted
            or product.status != 1
            or sku.status != 1
            or _available_stock(sku) <= 0
        )
        if unavailable:
            unavailables.append(
                UnavailableItem(
                    cart_item_id=item.id,
                    product_id=item.product_id,
                    sku_id=item.sku_id,
                    name=product.name if product else "",
                    sku_text=sku.sku_text if sku else "",
                ).model_dump(by_alias=True)
            )
            continue
        assert sku is not None and product is not None
        _validate_quantity(item.quantity, _available_stock(sku))
        preview_items.append(
            PreviewItemOut(
                cart_item_id=item.id,
                product_id=item.product_id,
                sku_id=item.sku_id,
                name=product.name,
                sku_text=sku.sku_text,
                price=float(sku.price),
                quantity=item.quantity,
                image=sku.image or product.main_image,
                stock=_available_stock(sku),
            ).model_dump(by_alias=True)
        )

    if unavailables:
        raise BizException(1203, "部分商品已下架或库存不足", {"unavailables": unavailables})

    amounts = _calc_amounts(preview_items)
    return PreviewOut(
        items=preview_items,
        total_amount=float(amounts["totalAmount"]),
        freight=float(amounts["freight"]),
        pay_amount=float(amounts["payAmount"]),
        addresses=_list_addresses_for_preview(db, user_id),
    ).model_dump(by_alias=True)


def preview_direct_order(db: Session, user_id: int, sku_id: int, quantity: int) -> dict:
    """直购结算预览（对齐 api-design §9.1 直购口径 / test-cases B5-3a）。"""
    product, sku = _get_saleable_sku(db, sku_id)
    _validate_quantity(quantity, _available_stock(sku))
    item = PreviewItemOut(
        cart_item_id=0,
        product_id=product.id,
        sku_id=sku.id,
        name=product.name,
        sku_text=sku.sku_text,
        price=float(sku.price),
        quantity=quantity,
        image=sku.image or product.main_image,
        stock=_available_stock(sku),
    ).model_dump(by_alias=True)
    amounts = _calc_amounts([item])
    return PreviewOut(
        items=[item],
        total_amount=float(amounts["totalAmount"]),
        freight=float(amounts["freight"]),
        pay_amount=float(amounts["payAmount"]),
        addresses=_list_addresses_for_preview(db, user_id),
    ).model_dump(by_alias=True)


def _build_product_items(db: Session, skus_qty: list[tuple[int, int]]) -> list[dict]:
    """校验并组装下单商品项（快照来源：实时 SKU/商品）。"""
    product_items: list[dict] = []
    for sku_id, quantity in skus_qty:
        product, sku = _get_saleable_sku(db, sku_id)
        _validate_quantity(quantity, _available_stock(sku))
        product_items.append(
            {
                "sku_id": sku.id,
                "product_id": product.id,
                "name": product.name,
                "sku_text": sku.sku_text,
                "price": float(sku.price),
                "quantity": quantity,
                "image": sku.image or product.main_image,
            }
        )
    return product_items


def create_order(
    db: Session, user_id: int, address_id: int, items: list[dict]
) -> dict:
    """创建订单（对齐 api-design §9.2 / test-cases B5-4）。
    同一事务：订单+明细+地址快照+库存预占+删除购物车项；金额服务端核算（不信任客户端）。
    """
    if not items:
        raise BizException(400, "订单商品不能为空")
    address = _get_address(db, user_id, address_id)
    product_items = _build_product_items(db, [(i["sku_id"], i["quantity"]) for i in items])
    sku_ids = [p["sku_id"] for p in product_items]

    _preoccupy_stock(db, product_items)
    _remove_cart_items(db, user_id, sku_ids)
    order = _build_order(db, user_id, address, product_items)
    db.commit()
    return _detail_dto(order, _order_items(db, order))


def create_direct_order(
    db: Session, user_id: int, address_id: int, sku_id: int, quantity: int
) -> dict:
    """直购下单（对齐 api-design §9.1 直购口径 / test-cases B5-3b）。
    不写/不删购物车项，其余与 create_order 一致。
    """
    address = _get_address(db, user_id, address_id)
    product_items = _build_product_items(db, [(sku_id, quantity)])
    _preoccupy_stock(db, product_items)
    order = _build_order(db, user_id, address, product_items)
    db.commit()
    return _detail_dto(order, _order_items(db, order))


def list_orders(
    db: Session, user_id: int, status: str | None, page: int, page_size: int
) -> dict:
    """订单列表（对齐 api-design §9.3 / test-cases B5-5）。"""
    rows, total = OrderRepository(db).list_by_user(user_id, status, page, page_size)
    grouped = _load_items(db, rows)
    return OrderListOut(
        items=[_list_item_dto(o, grouped.get(o.id, [])) for o in rows],
        total=total,
        page=page,
        pageSize=page_size,
        hasMore=page * page_size < total,
    ).model_dump(by_alias=True)


def _get_owned_order(db: Session, user_id: int, order_id: int) -> Order:
    """加载本人订单：不存在 404 / 越权 1403（对齐 test-cases B5-11/B5-13）。"""
    order = OrderRepository(db).get_owned(user_id, order_id)
    if order is None:
        if db.get(Order, order_id) is None:
            raise BizException(404, "订单不存在")
        raise BizException(1403, "订单归属不匹配")
    return order


def get_order_detail(db: Session, user_id: int, order_id: int) -> dict:
    """订单详情（对齐 api-design §9.4）。"""
    order = _get_owned_order(db, user_id, order_id)
    items = OrderItemRepository(db).list_by_order_ids([order.id])
    return _detail_dto(order, items)


def pay_order(db: Session, user_id: int, order_id: int, pay_type: str = "mock") -> dict:
    """支付订单（对齐 api-design §9.5 / test-cases B5-6）。
    - mock：直接置 paid；wechat（预留）：返回 payParams，不改状态
    - 重复支付 → 409
    """
    order = _get_owned_order(db, user_id, order_id)
    if order.status != "pending":
        raise BizException(409, "订单已支付，请勿重复支付")
    if pay_type == "wechat":
        return {
            "payParams": {
                "timeStamp": "1",
                "nonceStr": "mock",
                "package": "mock",
                "signType": "RSA",
                "paySign": "mock",
            }
        }
    order.status = "paid"
    order.pay_type = pay_type or "mock"
    order.pay_time = datetime.now()
    db.commit()
    return _detail_dto(order, _order_items(db, order))


def cancel_order(db: Session, user_id: int, order_id: int, reason: str | None = None) -> dict:
    """取消订单（对齐 api-design §9.6 / test-cases B5-7）。
    仅 pending 可取消；取消后回补锁定库存；非 pending → 1402。
    """
    order = _get_owned_order(db, user_id, order_id)
    if order.status != "pending":
        raise BizException(1402, "订单状态不允许该操作")
    _release_stock(db, order)
    order.status = "cancelled"
    order.cancel_reason = reason
    db.commit()
    return _detail_dto(order, _order_items(db, order))


def refund_order(
    db: Session,
    user_id: int,
    order_id: int,
    reason: str | None = None,
    refund_type: str | None = None,
) -> dict:
    """申请售后/退款（对齐 api-design §9.7 / test-cases B5-14）。
    仅 paid/shipped/completed 可申请；订单转 refund 并释放锁定库存；非三态 → 1402。
    """
    order = _get_owned_order(db, user_id, order_id)
    if order.status not in REFUNDABLE_STATUSES:
        raise BizException(1402, "订单状态不允许申请售后")
    _release_stock(db, order)
    original_status = order.status
    order.status = "refund"
    order.refund_reason = reason or "不符合预期"
    order.refund_type = refund_type or ("refund" if original_status == "paid" else "return")
    order.refund_time = datetime.now()
    db.commit()
    return _detail_dto(order, _order_items(db, order))


def remind_order(db: Session, user_id: int, order_id: int) -> dict:
    """提醒发货（对齐 api-design §9.8 / test-cases B5-8）。仅 paid 可调用。"""
    order = _get_owned_order(db, user_id, order_id)
    if order.status != "paid":
        raise BizException(1402, "订单状态不允许该操作")
    return {"reminded": True}


def confirm_order(db: Session, user_id: int, order_id: int) -> dict:
    """确认收货（对齐 api-design §9.9 / test-cases B5-9）。
    仅 shipped 可确认；置 completed、记 finish_time、发放积分（金额取整，预留）。
    """
    order = _get_owned_order(db, user_id, order_id)
    if order.status != "shipped":
        raise BizException(1402, "订单状态不允许该操作")
    order.status = "completed"
    order.finish_time = datetime.now()
    member = db.get(Member, user_id)
    if member is not None:
        member.points += int(order.pay_amount)
    db.commit()
    return _detail_dto(order, _order_items(db, order))


def buy_again(db: Session, user_id: int, order_id: int) -> dict:
    """再次购买（对齐 api-design §9.10 / test-cases B5-12）。
    用原订单明细（skuId）重新创建一笔 pending 订单；取默认地址，无地址 → 400。
    """
    order = _get_owned_order(db, user_id, order_id)
    address = _get_default_address(db, user_id)
    if address is None:
        raise BizException(400, "暂无收货地址，请先添加")
    items = OrderItemRepository(db).list_by_order_ids([order.id])
    product_items = _build_product_items(db, [(i.sku_id, i.quantity) for i in items])
    _preoccupy_stock(db, product_items)
    new_order = _build_order(db, user_id, address, product_items)
    db.commit()
    return _detail_dto(new_order, _order_items(db, new_order))


def order_stats(db: Session, user_id: int) -> dict:
    """订单状态角标（对齐 api-design §9.11 / test-cases B5-5）。"""
    return OrderStatsOut(**OrderRepository(db).stats_by_user(user_id)).model_dump(by_alias=True)
