"""订单模块业务逻辑：结算预览/下单/列表/详情/支付/取消/售后/提醒/收货/再次购买/角标。

对齐 docs/api-design.md §9 与 docs/test-cases.md B5（行为与前端 mock store.js 一致）。
金额一律 Decimal 计算，输出转 float；库存口径 = stock - lock_stock。
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BizException
from app.modules.address.models import ShippingAddress
from app.modules.auth.models import Member
from app.modules.cart.repository import CartRepository
from app.modules.coupon.models import (
    COUPON_TYPE_CASH,
    COUPON_TYPE_DISCOUNT,
    Coupon,
    UserCoupon,
)
from app.modules.order.models import (
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_PENDING,
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
from app.modules.points.models import (
    POINTS_BIZ_ORDER,
    POINTS_TYPE_CONSUME,
    POINTS_TYPE_EARN,
    PointsLog,
)
from app.modules.product.models import Product, ProductSku

logger = logging.getLogger("app.modules.order.service")

# 单次限购上限（对齐 error-code 1201）
ORDER_QUANTITY_MAX = 99

# 积分抵扣比例：每 POINTS_PER_YUAN 积分抵 1 元（对齐 PRD §4.x）
POINTS_PER_YUAN = 100

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


def _calc_amounts(
    product_items: list[dict],
    coupon: Coupon | None = None,
    points_used: int = 0,
) -> dict[str, Decimal]:
    """金额计算：商品总额 + 免邮 + 券/积分抵扣（对齐 mock calcOrderAmounts）。

    - 无券/无积分时行为与 P0 一致（payAmount == totalAmount）；
    - cash 满减：抵扣 amount；discount 折扣：按折扣率减免；
    - 积分抵扣：POINTS_PER_YUAN 积分抵 1 元，不超剩余应付。
    """
    total = sum((Decimal(str(p["price"])) * p["quantity"] for p in product_items), Decimal("0.00"))
    coupon_amount = Decimal("0.00")
    if coupon is not None:
        if coupon.type == COUPON_TYPE_CASH:
            coupon_amount = min(coupon.amount or Decimal("0.00"), total)
        elif coupon.type == COUPON_TYPE_DISCOUNT:
            discount = coupon.discount or Decimal("1.00")
            coupon_amount = total - (total * discount)
    points_amount = Decimal("0.00")
    if points_used > 0:
        points_amount = min(
            Decimal(points_used) / POINTS_PER_YUAN, total - coupon_amount
        )
    pay_amount = total - coupon_amount - points_amount
    return {
        "totalAmount": total,
        "freight": Decimal("0.00"),
        "couponAmount": coupon_amount,
        "pointsAmount": points_amount,
        "payAmount": pay_amount,
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


def _settle_stock(db: Session, order: Order) -> None:
    """支付成功转实扣：stock -= qty 且 lock_stock -= qty（对齐 PRD §4.x / api-design §9）。

    预占成功时已保证 stock - lock_stock >= qty，此处 max 仅为防御性下限。
    """
    items = OrderItemRepository(db).list_by_order_ids([order.id])
    for item in items:
        sku = db.get(ProductSku, item.sku_id)
        if sku:
            sku.stock = max(sku.stock - item.quantity, 0)
            sku.lock_stock = max(sku.lock_stock - item.quantity, 0)


def _resolve_coupon(
    db: Session,
    user_id: int,
    user_coupon_id: int | None,
    product_items: list[dict],
) -> Coupon | None:
    """校验并加载待核销优惠券（对齐 error-code 1601/1603/1604）。

    - 未传 userCouponId → 返回 None（不抵扣）；
    - 用户券不存在/非本人/非 unused → 1601；
    - 券停用/未到生效期/已过期 → 1603；
    - 不满足使用门槛 → 1604。
    """
    if user_coupon_id is None:
        return None
    uc = db.get(UserCoupon, user_coupon_id)
    if uc is None or uc.user_id != user_id or uc.status != "unused":
        raise BizException(1601, "优惠券不存在")
    coupon = db.get(Coupon, uc.coupon_id)
    if coupon is None or coupon.status != 1:
        raise BizException(1603, "优惠券已过期或未到生效期")
    now = datetime.now()
    if coupon.valid_start and now < coupon.valid_start:
        raise BizException(1603, "优惠券已过期或未到生效期")
    if coupon.valid_end and now > coupon.valid_end:
        raise BizException(1603, "优惠券已过期或未到生效期")
    total = sum(
        (Decimal(str(p["price"])) * p["quantity"] for p in product_items), Decimal("0.00")
    )
    if total < coupon.min_amount:
        raise BizException(1604, "不满足使用门槛")
    return coupon


def _consume_points(db: Session, user_id: int, points_used: int) -> None:
    """校验并扣减积分（对齐 error-code 1605）。积分不足 → 1605。"""
    if points_used <= 0:
        return
    member = db.get(Member, user_id)
    if member is None or (member.points or 0) < points_used:
        raise BizException(1605, "积分不足")
    member.points = (member.points or 0) - points_used
    db.add(
        PointsLog(
            user_id=user_id,
            change=-points_used,
            balance=member.points,
            type=POINTS_TYPE_CONSUME,
            biz_type=POINTS_BIZ_ORDER,
            remark="订单积分抵扣",
        )
    )


def _mark_coupon_used(db: Session, user_id: int, user_coupon_id: int, order_no: str) -> None:
    """核销用户券：置 used、记订单号与使用时间。"""
    uc = db.get(UserCoupon, user_coupon_id)
    if uc is not None and uc.user_id == user_id and uc.status == "unused":
        uc.status = "used"
        uc.used_order_no = order_no
        uc.used_at = datetime.now()


def _build_order(
    db: Session,
    user_id: int,
    address: ShippingAddress,
    product_items: list[dict],
    coupon: Coupon | None = None,
    points_used: int = 0,
) -> Order:
    """创建订单主表 + 明细（快照），挂载到 Session（由调用方 commit）。"""
    amounts = _calc_amounts(product_items, coupon, points_used)
    order = Order(
        order_no=_gen_order_no(datetime.now()),
        user_id=user_id,
        status="pending",
        total_amount=amounts["totalAmount"],
        freight=amounts["freight"],
        coupon_amount=amounts["couponAmount"],
        points_used=int(amounts["pointsAmount"] * POINTS_PER_YUAN),
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
        coupon_amount=float(order.coupon_amount),
        points_used=order.points_used,
        pay_amount=float(order.pay_amount),
        receiver=_receiver_dto(order),
        items=_order_item_dtos(items),
        create_time=_fmt_dt(order.created_at) or "",
        pay_deadline=_pay_deadline(order),
        available_actions=_compute_actions(order.status),
    ).model_dump(by_alias=True)


def _pay_deadline(order: Order) -> str | None:
    """待支付订单的支付截止时间（ISO 字符串）；非 pending 返回 None。"""
    if order.status != ORDER_STATUS_PENDING or order.created_at is None:
        return None
    deadline = order.created_at + timedelta(seconds=settings.order_timeout_seconds)
    return deadline.isoformat()


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
        coupon_amount=float(amounts["couponAmount"]),
        points_amount=float(amounts["pointsAmount"]),
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
        coupon_amount=float(amounts["couponAmount"]),
        points_amount=float(amounts["pointsAmount"]),
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
    db: Session,
    user_id: int,
    address_id: int,
    items: list[dict],
    user_coupon_id: int | None = None,
    points_used: int = 0,
) -> dict:
    """创建订单（对齐 api-design §9.2 / test-cases B5-4）。
    同一事务：订单+明细+地址快照+库存预占+删除购物车项；金额服务端核算（不信任客户端）。
    可选：核销优惠券（userCouponId）、积分抵扣（pointsUsed）。
    """
    if not items:
        raise BizException(400, "订单商品不能为空")
    address = _get_address(db, user_id, address_id)
    product_items = _build_product_items(db, [(i["sku_id"], i["quantity"]) for i in items])
    sku_ids = [p["sku_id"] for p in product_items]

    coupon = _resolve_coupon(db, user_id, user_coupon_id, product_items)
    _consume_points(db, user_id, points_used)

    _preoccupy_stock(db, product_items)
    _remove_cart_items(db, user_id, sku_ids)
    order = _build_order(db, user_id, address, product_items, coupon, points_used)
    if coupon is not None and user_coupon_id is not None:
        _mark_coupon_used(db, user_id, user_coupon_id, order.order_no)
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
    after_sale_text = _after_sale_text_by_order(db, rows)
    items = []
    for o in rows:
        dto = _list_item_dto(o, grouped.get(o.id, []))
        if o.status == "refund" and after_sale_text.get(o.id):
            dto["statusText"] = after_sale_text[o.id]
        items.append(dto)
    return OrderListOut(
        items=items,
        total=total,
        page=page,
        pageSize=page_size,
        hasMore=page * page_size < total,
    ).model_dump(by_alias=True)


def _after_sale_text_by_order(db: Session, orders: list[Order]) -> dict[int, str]:
    """批量查询 refund 订单的最新售后工单状态文案（order_id → statusText），供列表覆盖使用。"""
    from app.modules.after_sale.models import AFTER_SALE_STATUS_TEXT, AfterSale

    refund_ids = [o.id for o in orders if o.status == "refund"]
    if not refund_ids:
        return {}
    # 每订单取最新一条工单：采用 id 最大的一行（状态覆盖口径同详情页）
    rows = db.execute(
        select(AfterSale.order_id, AfterSale.status)
        .where(AfterSale.order_id.in_(refund_ids))
        .order_by(AfterSale.id.desc())
    ).all()
    result: dict[int, str] = {}
    for order_id, status in rows:
        if order_id not in result:
            result[order_id] = AFTER_SALE_STATUS_TEXT.get(status, "售后中")
    return result


def _get_owned_order(db: Session, user_id: int, order_id: int) -> Order:
    """加载本人订单：不存在 404 / 越权 1403（对齐 test-cases B5-11/B5-13）。"""
    order = OrderRepository(db).get_owned(user_id, order_id)
    if order is None:
        if db.get(Order, order_id) is None:
            raise BizException(404, "订单不存在")
        raise BizException(1403, "订单归属不匹配")
    return order


def _apply_after_sale_progress(db: Session, order_id: int, dto: dict) -> None:
    """refund 订单按最新售后工单状态覆盖状态文案。

    后台审核通过（approved）/驳回（rejected）后，小程序刷新订单详情即可看到更新。
    `statusText` 与列表口径一致（见 api-design §9.3：申请中/已通过/已驳回/已退款/已关闭），
    `statusDesc` 提供详情页的补充说明，避免同笔售后在列表与详情显示不同状态。
    """
    from app.modules.after_sale.models import (
        AFTER_SALE_APPLYING,
        AFTER_SALE_APPROVED,
        AFTER_SALE_REFUNDED,
        AFTER_SALE_REJECTED,
        AFTER_SALE_STATUS_TEXT,
        AfterSale,
    )

    item = db.scalars(
        select(AfterSale)
        .where(AfterSale.order_id == order_id)
        .order_by(AfterSale.id.desc())
    ).first()
    if item is None:
        return
    dto["statusText"] = AFTER_SALE_STATUS_TEXT.get(item.status, "售后中")
    dto["statusDesc"] = {
        AFTER_SALE_APPLYING: "退款申请已提交，请耐心等待平台审核",
        AFTER_SALE_APPROVED: "退款申请已通过，款项将原路退回",
        AFTER_SALE_REJECTED: "退款申请未通过：" + (item.audit_remark or "请查看平台审核意见"),
        AFTER_SALE_REFUNDED: "退款已完成，款项已原路退回",
    }.get(item.status, "")


def get_order_detail(db: Session, user_id: int, order_id: int) -> dict:
    """订单详情（对齐 api-design §9.4）。"""
    order = _get_owned_order(db, user_id, order_id)
    items = OrderItemRepository(db).list_by_order_ids([order.id])
    dto = _detail_dto(order, items)
    if order.status == "refund":
        _apply_after_sale_progress(db, order.id, dto)
    return dto


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
    _settle_stock(db, order)
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
        earned = int(order.pay_amount)
        member.points = (member.points or 0) + earned
        db.add(
            PointsLog(
                user_id=user_id,
                change=earned,
                balance=member.points,
                type=POINTS_TYPE_EARN,
                biz_type=POINTS_BIZ_ORDER,
                remark="订单完成获得积分",
            )
        )
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


def close_timeout_orders(db: Session, *, now: datetime | None = None) -> int:
    """关闭超时未支付订单并回补锁定库存（对齐 PRD §4.2 / api-design §16.4）。

    - 扫描 status=pending 且 created_at 早于（now - 超时阈值）的订单；
    - 逐单置 cancelled、记 cancel_reason，并回补 lock_stock（幂等：仅处理 pending）；
    - 返回本次关闭的订单数；单次批量上限由 repository 控制，可多次调用直至返回 0。
    """
    now = now or datetime.now()
    before = now - timedelta(seconds=settings.order_timeout_seconds)
    orders = OrderRepository(db).list_timeout_pending(before)
    if not orders:
        return 0
    for order in orders:
        if order.status != ORDER_STATUS_PENDING:
            continue
        _release_stock(db, order)
        order.status = ORDER_STATUS_CANCELLED
        order.cancel_reason = "订单超时未支付，系统自动关闭"
    db.commit()
    return len(orders)
