"""订单模块单元测试：结算预览、下单、列表、支付、取消、售后、收货、再次购买、角标。

对齐 docs/test-cases.md B5。使用内存 Fake 仓储/桩验证 service 业务分支（模式同 test_cart.py）。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.auth.models import Member
from app.modules.coupon.models import Coupon, UserCoupon
from app.modules.order import service
from app.modules.order.models import Order, OrderItem
from app.modules.points.models import PointsLog
from app.modules.product.models import Product, ProductSku


def _sku(
    id: int,
    *,
    product_id: int = 1,
    price: str = "100.00",
    stock: int = 50,
    lock_stock: int = 0,
    status: int = 1,
    deleted: bool = False,
    sku_text: str = "白；40",
    image: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        product_id=product_id,
        price=Decimal(price),
        stock=stock,
        lock_stock=lock_stock,
        status=status,
        deleted=deleted,
        sku_text=sku_text,
        image=image,
    )


def _product(
    id: int, *, status: int = 1, deleted: bool = False, name: str = "城市慢跑鞋"
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id, status=status, deleted=deleted, name=name, main_image="/img.jpg"
    )


def _cart(
    id: int,
    *,
    user_id: int = 1,
    product_id: int = 1,
    sku_id: int = 10,
    quantity: int = 1,
    selected: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        user_id=user_id,
        product_id=product_id,
        sku_id=sku_id,
        quantity=quantity,
        selected=selected,
    )


def _address(
    id: int,
    *,
    user_id: int = 1,
    name: str = "王小悦",
    is_default: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        user_id=user_id,
        name=name,
        phone="13812345678",
        province="上海市",
        city="上海市",
        district="浦东新区",
        detail="张江高科技园区 501 室",
        is_default=is_default,
        deleted=False,
    )


def _order_item(
    id: int, sku_id: int, *, quantity: int = 1, price: str = "100.00"
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        sku_id=sku_id,
        product_name="城市慢跑鞋",
        sku_text="白；40",
        price=Decimal(price),
        quantity=quantity,
        image="/img.jpg",
    )


def _order(
    id: int,
    *,
    user_id: int = 1,
    status: str = "pending",
    items: list[SimpleNamespace] | None = None,
    pay_amount: str = "100.00",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        order_no=f"K20260901000000{id:03d}",
        user_id=user_id,
        status=status,
        total_amount=Decimal(pay_amount),
        freight=Decimal("0.00"),
        coupon_amount=Decimal("0.00"),
        points_used=0,
        pay_amount=Decimal(pay_amount),
        receiver_name="王小悦",
        receiver_phone="13812345678",
        receiver_region="上海市 上海市 浦东新区",
        receiver_detail="张江高科技园区 501 室",
        pay_type=None,
        pay_time=None,
        ship_time=None,
        finish_time=None,
        created_at=datetime(2026, 9, 1, 10, 0, 0),
        items=items or [],
    )


class FakeDb:
    """内存 Session：支持 get(Product/ProductSku/Member/Order) 与 add/flush/commit。"""

    def __init__(
        self,
        skus: dict[int, SimpleNamespace],
        products: dict[int, SimpleNamespace],
        *,
        orders: dict[int, SimpleNamespace] | None = None,
        order_items: dict[int, list[SimpleNamespace]] | None = None,
        member: SimpleNamespace | None = None,
        coupons: dict[int, SimpleNamespace] | None = None,
        user_coupons: dict[int, SimpleNamespace] | None = None,
    ) -> None:
        self._skus = skus
        self._products = products
        self._member = member
        self._orders: dict[int, SimpleNamespace] = orders or {}
        self._order_items: dict[int, list] = order_items or {}
        self._coupons: dict[int, SimpleNamespace] = coupons or {}
        self._user_coupons: dict[int, SimpleNamespace] = user_coupons or {}
        self._points_logs: list[SimpleNamespace] = []
        self._pending: list[object] = []
        self._next_order_id = 100
        self._next_item_id = 900
        self.commits = 0

    def get(self, model: type, pk: int) -> object | None:
        if model is ProductSku:
            return self._skus.get(pk)
        if model is Product:
            return self._products.get(pk)
        if model is Member:
            return self._member
        if model is Order:
            return self._orders.get(pk)
        if model is Coupon:
            return self._coupons.get(pk)
        if model is UserCoupon:
            return self._user_coupons.get(pk)
        return None

    def add(self, obj: object) -> None:
        if isinstance(obj, PointsLog):
            self._points_logs.append(obj)
        else:
            self._pending.append(obj)

    def flush(self) -> None:
        for obj in self._pending:
            if isinstance(obj, Order):
                obj.id = self._next_order_id
                self._next_order_id += 1
                self._orders[obj.id] = obj
                self._order_items.setdefault(obj.id, [])
            elif isinstance(obj, OrderItem):
                obj.id = self._next_item_id
                self._next_item_id += 1
                self._order_items.setdefault(obj.order_id, []).append(obj)
            elif isinstance(obj, PointsLog):
                self._points_logs.append(obj)
        self._pending = []

    def commit(self) -> None:
        self.commits += 1


class FakeOrderRepo:
    """内存订单仓储。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db

    def list_by_user(
        self, user_id: int, status: str | None, page: int, page_size: int
    ) -> tuple[list[SimpleNamespace], int]:
        rows = [o for o in self.db._orders.values() if o.user_id == user_id]
        if status:
            rows = [o for o in rows if o.status == status]
        total = len(rows)
        start = (page - 1) * page_size
        return rows[start : start + page_size], total

    def get_owned(self, user_id: int, order_id: int) -> SimpleNamespace | None:
        order = self.db._orders.get(order_id)
        if order is not None and order.user_id == user_id:
            return order
        return None

    def list_timeout_pending(self, before: datetime, limit: int = 200) -> list[SimpleNamespace]:
        rows = [
            o
            for o in self.db._orders.values()
            if o.status == "pending" and o.created_at < before
        ]
        rows.sort(key=lambda o: o.created_at)
        return rows[:limit]

    def stats_by_user(self, user_id: int) -> dict[str, int]:
        stats = {s: 0 for s in ("pending", "paid", "shipped", "refund")}
        for o in self.db._orders.values():
            if o.user_id == user_id and o.status in stats:
                stats[o.status] += 1
        return stats


class FakeOrderItemRepo:
    """内存订单明细仓储。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db

    def list_by_order_ids(self, order_ids: list[int]) -> list[SimpleNamespace]:
        rows: list[SimpleNamespace] = []
        for oid in order_ids:
            for item in self.db._order_items.get(oid, []):
                if not hasattr(item, "order_id"):
                    item.order_id = oid
                rows.append(item)
        return rows


class FakeCartRepo:
    """内存购物车仓储（替代 service 引用的 CartRepository）。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db
        self.rows: list[SimpleNamespace] = []

    def list_by_user(self, user_id: int) -> list[SimpleNamespace]:
        return [c for c in self.rows if c.user_id == user_id]

    def delete_by_skus(self, user_id: int, sku_ids: list[int]) -> int:
        before = len(self.rows)
        self.rows = [
            c
            for c in self.rows
            if not (c.user_id == user_id and c.sku_id in sku_ids)
        ]
        return before - len(self.rows)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> tuple[FakeDb, FakeCartRepo, dict[int, SimpleNamespace]]:
    db = FakeDb(
        skus={
            10: _sku(10),
            11: _sku(11, sku_text="黑；41"),
            20: _sku(20, product_id=2, price="200.00"),
        },
        products={1: _product(1), 2: _product(2, name="帆布鞋")},
        member=SimpleNamespace(id=1, points=0),
        orders={
            1001: _order(1001, status="paid", items=[_order_item(901, 10)]),
            1002: _order(1002, status="shipped", items=[_order_item(902, 11)]),
            1003: _order(1003, status="pending", items=[_order_item(903, 20)]),
        },
        order_items={
            1001: [_order_item(901, 10)],
            1002: [_order_item(902, 11)],
            1003: [_order_item(903, 20)],
        },
    )
    cart_repo = FakeCartRepo(db)
    cart_repo.rows = [_cart(1, sku_id=10, quantity=1, selected=True)]

    addresses = {1: _address(1), 2: _address(2, is_default=False)}

    monkeypatch.setattr(service, "OrderRepository", lambda d: FakeOrderRepo(d))
    monkeypatch.setattr(service, "OrderItemRepository", lambda d: FakeOrderItemRepo(d))
    monkeypatch.setattr(service, "CartRepository", lambda d: cart_repo)
    monkeypatch.setattr(
        service,
        "_remove_cart_items",
        lambda d, uid, skus: cart_repo.delete_by_skus(uid, skus),
    )

    def _fake_get_address(d: object, uid: int, aid: int) -> SimpleNamespace:
        if aid in addresses:
            return addresses[aid]
        raise BizException(404, "地址不存在")

    monkeypatch.setattr(service, "_get_address", _fake_get_address)
    monkeypatch.setattr(
        service, "_get_default_address", lambda d, uid: addresses.get(1)
    )
    monkeypatch.setattr(
        service,
        "_list_addresses_for_preview",
        lambda d, uid: [
            {
                "id": a.id,
                "name": a.name,
                "phone": a.phone,
                "regionText": f"{a.province} {a.city} {a.district}",
                "detail": a.detail,
                "isDefault": a.is_default,
            }
            for a in addresses.values()
        ],
    )
    return db, cart_repo, addresses


# ---- B5-1 结算预览 ----

def test_preview_requires_selection(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, cart_repo, _ = env
    cart_repo.rows = []
    with pytest.raises(BizException) as e:
        service.preview_order(db, 1)
    assert e.value.code == 400


def test_preview_ok(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, cart_repo, _ = env
    cart_repo.rows = [
        _cart(1, sku_id=10, quantity=2, selected=True),  # 100*2
        _cart(2, sku_id=11, quantity=1, selected=False),  # 未勾选不计
    ]
    data = service.preview_order(db, 1)
    assert len(data["items"]) == 1
    assert data["items"][0]["skuId"] == 10
    assert data["totalAmount"] == 200.0
    assert data["payAmount"] == 200.0
    assert data["freight"] == 0.0
    assert len(data["addresses"]) == 2


def test_preview_with_cart_item_ids(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, cart_repo, _ = env
    cart_repo.rows = [
        _cart(1, sku_id=10, quantity=1, selected=True),
        _cart(2, sku_id=11, quantity=3, selected=True),
    ]
    data = service.preview_order(db, 1, "2")
    assert len(data["items"]) == 1
    assert data["items"][0]["skuId"] == 11


# ---- B5-2 预览含失效项 ----

def test_preview_unavailable_1203(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, cart_repo, _ = env
    db._skus[10] = _sku(10, status=0)  # 停售
    cart_repo.rows = [_cart(1, sku_id=10, quantity=1, selected=True)]
    with pytest.raises(BizException) as e:
        service.preview_order(db, 1)
    assert e.value.code == 1203
    assert e.value.data["unavailables"][0]["skuId"] == 10


# ---- B5-3 预览库存不足 ----

def test_preview_stock_1104(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, cart_repo, _ = env
    db._skus[10] = _sku(10, stock=1, lock_stock=0)  # 可用 1
    cart_repo.rows = [_cart(1, sku_id=10, quantity=2, selected=True)]
    with pytest.raises(BizException) as e:
        service.preview_order(db, 1)
    assert e.value.code == 1104
    assert e.value.data["availableStock"] == 1


# ---- B5-3a 直购预览 ----

def test_preview_direct_ok(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    data = service.preview_direct_order(db, 1, 10, 2)
    assert len(data["items"]) == 1
    assert data["items"][0]["skuId"] == 10
    assert data["items"][0]["quantity"] == 2
    assert data["payAmount"] == 200.0


# ---- B5-3b 直购下单 ----

def test_create_direct_no_address_404(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.create_direct_order(db, 1, 999, 10, 1)
    assert e.value.code == 404


def test_create_direct_ok(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, cart_repo, _ = env
    before = len(cart_repo.rows)
    data = service.create_direct_order(db, 1, 1, 10, 2)
    assert data["status"] == "pending"
    assert data["payAmount"] == 200.0
    assert data["receiver"]["name"] == "王小悦"
    # 不写/不删购物车项
    assert len(cart_repo.rows) == before
    # 库存已预占
    assert db._skus[10].lock_stock == 2


# ---- B5-4 创建订单 ----

def test_create_order_ok(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, cart_repo, _ = env
    cart_repo.rows = [
        _cart(1, sku_id=10, quantity=1, selected=True),
        _cart(2, sku_id=11, quantity=1, selected=True),
    ]
    items = [{"sku_id": 10, "quantity": 2}, {"sku_id": 11, "quantity": 1}]
    data = service.create_order(db, 1, 1, items)
    assert data["status"] == "pending"
    assert data["totalAmount"] == 300.0
    assert len(data["items"]) == 2
    # 同一事务：地址快照
    assert data["receiver"]["regionText"] == "上海市 上海市 浦东新区"
    # 库存预占
    assert db._skus[10].lock_stock == 2
    assert db._skus[11].lock_stock == 1
    # 购物车项已删除（幂等：仅清本次结算 sku）
    assert all(c.sku_id not in (10, 11) for c in cart_repo.rows)


def test_create_order_empty_items_400(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.create_order(db, 1, 1, [])
    assert e.value.code == 400


# ---- B5-5 列表筛选/分页/角标 ----

def test_list_orders_filter_pagination(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    data = service.list_orders(db, 1, "paid", 1, 10)
    assert len(data["list"]) == 1
    assert data["list"][0]["status"] == "paid"
    assert data["total"] == 1
    assert data["hasMore"] is False
    assert data["list"][0]["statusText"] == "待发货"
    assert data["list"][0]["availableActions"] == ["remind", "refund", "buyAgain"]
    # 空筛选 → 全部
    all_data = service.list_orders(db, 1, None, 1, 10)
    assert all_data["total"] == 3
    # 分页
    paged = service.list_orders(db, 1, None, 1, 2)
    assert len(paged["list"]) == 2
    assert paged["hasMore"] is True


def test_order_stats(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    stats = service.order_stats(db, 1)
    assert stats == {"pending": 1, "paid": 1, "shipped": 1, "refund": 0}


# ---- B5-6 支付 ----

def test_pay_ok(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._skus[20].lock_stock = 1  # 模拟下单已预占 1 件
    data = service.pay_order(db, 1, 1003)
    assert data["status"] == "paid"
    assert data["payType"] == "mock"
    assert data["payTime"] is not None
    assert db._skus[20].stock == 49  # 支付成功转实扣
    assert db._skus[20].lock_stock == 0  # 释放锁定


def test_pay_repeat_409(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.pay_order(db, 1, 1001)  # 已 paid
    assert e.value.code == 409


# ---- B5-7 取消回补 ----

def test_cancel_ok_release_stock(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._skus[20].lock_stock = 5
    data = service.cancel_order(db, 1, 1003, "不想要了")
    assert data["status"] == "cancelled"
    assert db._skus[20].lock_stock == 4  # 回补 1


def test_cancel_non_pending_1402(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.cancel_order(db, 1, 1001)  # paid
    assert e.value.code == 1402


# ---- B5-8 提醒发货 ----

def test_remind_ok(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    assert service.remind_order(db, 1, 1001) == {"reminded": True}


def test_remind_non_paid_1402(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.remind_order(db, 1, 1002)  # shipped
    assert e.value.code == 1402


# ---- B5-9 确认收货 ----

def test_confirm_ok_points(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    data = service.confirm_order(db, 1, 1002)
    assert data["status"] == "completed"
    assert data["finishTime"] is not None
    assert db._member.points == 100  # 积分累加（金额取整）


def test_confirm_non_shipped_1402(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.confirm_order(db, 1, 1001)  # paid
    assert e.value.code == 1402


# ---- B5-10 状态机非法流转 ----

def test_cancel_after_pay_1402(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.cancel_order(db, 1, 1001)
    assert e.value.code == 1402


# ---- B5-11 越权订单 ----

def test_unauthorized_order_1403(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._orders[1009] = _order(1009, user_id=2, status="pending")
    with pytest.raises(BizException) as e:
        service.get_order_detail(db, 1, 1009)
    assert e.value.code == 1403


# ---- B5-13 订单不存在 ----

def test_order_not_found_404(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.get_order_detail(db, 1, 9999)
    assert e.value.code == 404


# ---- B5-12 再次购买 ----

def test_buy_again_ok(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    data = service.buy_again(db, 1, 1001)
    assert data["status"] == "pending"
    assert data["id"] != 1001
    assert len(data["items"]) == 1
    assert db._skus[10].lock_stock == 1  # 新订单预占


def test_buy_again_no_address_400(
    env: tuple[FakeDb, FakeCartRepo, dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    db, _, _ = env
    monkeypatch.setattr(service, "_get_default_address", lambda d, uid: None)
    with pytest.raises(BizException) as e:
        service.buy_again(db, 1, 1001)
    assert e.value.code == 400


# ---- B5-14 售后/退款 ----

def test_refund_ok_restore_stock(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._skus[10].stock = 49  # 模拟支付已实扣 1 件（stock 50 → 49）
    data = service.refund_order(db, 1, 1001, "不符合预期", "refund")
    assert data["status"] == "refund"
    assert db._skus[10].stock == 50  # 退款回补已实扣库存


def test_refund_default_type_by_status(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    service.refund_order(db, 1, 1001)  # paid → 默认 refund
    assert db._orders[1001].refund_type == "refund"
    service.refund_order(db, 1, 1002)  # shipped → 默认 return
    assert db._orders[1002].refund_type == "return"


def test_refund_non_refundable_1402(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    with pytest.raises(BizException) as e:
        service.refund_order(db, 1, 1003)  # pending
    assert e.value.code == 1402


def test_refund_repeat_1402(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    service.refund_order(db, 1, 1001)
    with pytest.raises(BizException) as e:
        service.refund_order(db, 1, 1001)  # 已是 refund
    assert e.value.code == 1402


# ---- B5-15 超时未支付自动关闭 ----

def test_close_timeout_orders_closes_and_releases(
    env: tuple[FakeDb, FakeCartRepo, dict],
) -> None:
    db, _, _ = env
    db._skus[20].lock_stock = 1  # 模拟下单已预占 1 件
    db._orders[1003].created_at = datetime(2026, 9, 1, 8, 0, 0)  # 超 2h
    now = datetime(2026, 9, 1, 11, 0, 0)
    closed = service.close_timeout_orders(db, now=now)
    assert closed == 1
    assert db._orders[1003].status == "cancelled"
    assert db._orders[1003].cancel_reason == "订单超时未支付，系统自动关闭"
    assert db._skus[20].lock_stock == 0  # 回补锁定库存


def test_close_timeout_orders_skips_fresh(
    env: tuple[FakeDb, FakeCartRepo, dict],
) -> None:
    db, _, _ = env
    db._orders[1003].created_at = datetime(2026, 9, 1, 8, 0, 0)  # 超 2h
    fresh = _order(1004, status="pending", items=[_order_item(904, 20)])
    fresh.created_at = datetime(2026, 9, 1, 10, 0, 0)  # 未超 2h
    db._orders[1004] = fresh
    db._order_items[1004] = [_order_item(904, 20)]
    now = datetime(2026, 9, 1, 11, 0, 0)
    closed = service.close_timeout_orders(db, now=now)
    assert closed == 1  # 仅关闭 1003
    assert db._orders[1004].status == "pending"


def test_close_timeout_orders_idempotent(
    env: tuple[FakeDb, FakeCartRepo, dict],
) -> None:
    db, _, _ = env
    db._orders[1003].created_at = datetime(2026, 9, 1, 8, 0, 0)  # 超 2h
    now = datetime(2026, 9, 1, 11, 0, 0)
    assert service.close_timeout_orders(db, now=now) == 1
    assert service.close_timeout_orders(db, now=now) == 0  # 重复执行无害


# ---- B5-4a 优惠券/积分抵扣下单 ----

def _coupon(
    id: int,
    *,
    type: str = "cash",
    amount: str = "20.00",
    discount: str | None = None,
    min_amount: str = "0.00",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        type=type,
        amount=Decimal(amount),
        discount=Decimal(discount) if discount else None,
        min_amount=Decimal(min_amount),
        status=1,
        valid_start=None,
        valid_end=None,
    )


def _user_coupon(
    id: int, *, user_id: int = 1, coupon_id: int = 1, status: str = "unused"
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        user_id=user_id,
        coupon_id=coupon_id,
        status=status,
        used_order_no=None,
        used_at=None,
    )


def test_create_order_with_coupon(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._coupons[1] = _coupon(1, amount="20.00")
    db._user_coupons[100] = _user_coupon(100, coupon_id=1)
    items = [{"sku_id": 10, "quantity": 1}]  # 100 元
    data = service.create_order(db, 1, 1, items, user_coupon_id=100)
    assert data["payAmount"] == 80.0
    assert data["couponAmount"] == 20.0
    assert db._user_coupons[100].status == "used"
    assert db._user_coupons[100].used_order_no == data["orderNo"]


def test_create_order_coupon_not_found(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    items = [{"sku_id": 10, "quantity": 1}]
    with pytest.raises(BizException) as e:
        service.create_order(db, 1, 1, items, user_coupon_id=999)
    assert e.value.code == 1601


def test_create_order_coupon_min_amount(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._coupons[1] = _coupon(1, amount="20.00", min_amount="200.00")
    db._user_coupons[100] = _user_coupon(100, coupon_id=1)
    items = [{"sku_id": 10, "quantity": 1}]  # 100 元 < 门槛 200
    with pytest.raises(BizException) as e:
        service.create_order(db, 1, 1, items, user_coupon_id=100)
    assert e.value.code == 1604


def test_create_order_with_points(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._member = SimpleNamespace(id=1, points=500)
    items = [{"sku_id": 10, "quantity": 1}]  # 100 元
    data = service.create_order(db, 1, 1, items, points_used=100)  # 100 积分抵 1 元
    assert data["payAmount"] == 99.0
    assert db._member.points == 400
    assert len(db._points_logs) == 1
    assert db._points_logs[0].change == -100


def test_create_order_points_insufficient(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._member = SimpleNamespace(id=1, points=50)
    items = [{"sku_id": 10, "quantity": 1}]
    with pytest.raises(BizException) as e:
        service.create_order(db, 1, 1, items, points_used=100)
    assert e.value.code == 1605


def test_confirm_order_earns_points(env: tuple[FakeDb, FakeCartRepo, dict]) -> None:
    db, _, _ = env
    db._member = SimpleNamespace(id=1, points=0)
    db._orders[1002].status = "shipped"
    db._orders[1002].pay_amount = Decimal("100.00")
    data = service.confirm_order(db, 1, 1002)
    assert data["status"] == "completed"
    assert db._member.points == 100
    assert len(db._points_logs) == 1
    assert db._points_logs[0].change == 100
    assert db._points_logs[0].type == "earn"
