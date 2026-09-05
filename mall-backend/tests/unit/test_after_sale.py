"""售后工单模块单元测试：申请、列表、详情。

对齐 docs/test-cases.md B5-14 / B8（售后）。使用内存 Fake 仓储/桩验证 service 业务分支。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.after_sale import service
from app.modules.after_sale.models import AfterSale
from app.modules.after_sale.schemas import CreateAfterSaleRequest
from app.modules.order.models import Order


def _order(
    id: int,
    *,
    user_id: int = 1,
    status: str = "paid",
    pay_amount: str = "100.00",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        user_id=user_id,
        status=status,
        pay_amount=Decimal(pay_amount),
    )


def _after_sale(
    id: int,
    *,
    order_id: int = 1,
    user_id: int = 1,
    type: str = "refund",
    reason: str = "商品破损",
    amount: str = "100.00",
    status: str = "applying",
    images: list | None = None,
    audit_remark: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        order_id=order_id,
        user_id=user_id,
        type=type,
        reason=reason,
        amount=Decimal(amount),
        status=status,
        images=images,
        audit_remark=audit_remark,
        created_at=datetime(2026, 9, 1, 10, 0, 0),
    )


class FakeDb:
    """内存 Session：支持 get(Order/AfterSale)、scalars、add/flush/commit。"""

    def __init__(
        self,
        orders: dict[int, SimpleNamespace],
        after_sales: dict[int, SimpleNamespace] | None = None,
    ) -> None:
        self._orders = orders
        self._after_sales: dict[int, SimpleNamespace] = after_sales or {}
        self._pending: list[object] = []
        self._next_id = 100
        self.commits = 0

    def get(self, model: type, pk: int) -> object | None:
        if model is Order:
            return self._orders.get(pk)
        if model is AfterSale:
            return self._after_sales.get(pk)
        return None

    def scalars(self, stmt: object) -> object:
        class _Result:
            def __init__(self, rows: list[SimpleNamespace]) -> None:
                self._rows = rows

            def first(self) -> SimpleNamespace | None:
                return self._rows[0] if self._rows else None

        return _Result(list(self._after_sales.values()))

    def add(self, obj: object) -> None:
        self._pending.append(obj)

    def flush(self) -> None:
        for obj in self._pending:
            if isinstance(obj, AfterSale):
                obj.id = self._next_id
                obj.created_at = datetime(2026, 9, 1, 10, 0, 0)
                self._next_id += 1
                self._after_sales[obj.id] = obj
        self._pending = []

    def commit(self) -> None:
        self.commits += 1


class FakeAfterSaleRepo:
    """内存售后单仓储。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db

    def list_by_user(
        self, user_id: int, status: str | None, page: int, page_size: int
    ) -> tuple[list[SimpleNamespace], int]:
        rows = [r for r in self.db._after_sales.values() if r.user_id == user_id]
        if status:
            rows = [r for r in rows if r.status == status]
        rows.sort(key=lambda r: r.id, reverse=True)
        total = len(rows)
        start = (page - 1) * page_size
        return rows[start : start + page_size], total


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> FakeDb:
    db = FakeDb(
        orders={
            1: _order(1),
            2: _order(2, status="pending"),
            3: _order(3, user_id=2),
            4: _order(4, status="shipped"),
        },
        after_sales={},
    )
    monkeypatch.setattr(service, "AfterSaleRepository", lambda d: FakeAfterSaleRepo(d))
    monkeypatch.setattr(service, "_restore_stock", lambda db, order: None)
    return db


# ---- B5-14a 申请售后 ----

def test_create_after_sale_ok(env: FakeDb) -> None:
    db = env
    body = CreateAfterSaleRequest(order_id=1, type="refund", reason="商品破损")
    item = service.create_after_sale(db, 1, body)
    assert item.id == 100
    assert item.status == "applying"
    assert item.amount == 100.0  # 默认取订单实付金额
    assert db._after_sales[100].order_id == 1
    # 联动订单转售后中
    assert db._orders[1].status == "refund"
    assert db._orders[1].refund_reason == "商品破损"
    assert db._orders[1].refund_type == "refund"


def test_create_after_sale_default_type_paid(env: FakeDb) -> None:
    """paid → refund(仅退款)。"""
    service.create_after_sale(env, 1, CreateAfterSaleRequest(order_id=1, type="refund", reason="x"))
    assert env._orders[1].refund_type == "refund"


def test_create_after_sale_default_type_shipped(env: FakeDb) -> None:
    """shipped → return(退货退款)。"""
    service.create_after_sale(env, 1, CreateAfterSaleRequest(order_id=4, type="refund", reason="x"))
    assert env._orders[4].refund_type == "return"


def test_create_after_sale_custom_amount(env: FakeDb) -> None:
    db = env
    body = CreateAfterSaleRequest(order_id=1, type="refund", reason="部分退款", amount=50.0)
    item = service.create_after_sale(db, 1, body)
    assert item.amount == 50.0


def test_create_after_sale_order_not_found(env: FakeDb) -> None:
    body = CreateAfterSaleRequest(order_id=999, type="refund", reason="x")
    with pytest.raises(BizException) as e:
        service.create_after_sale(env, 1, body)
    assert e.value.code == 404


def test_create_after_sale_not_owned(env: FakeDb) -> None:
    body = CreateAfterSaleRequest(order_id=3, type="refund", reason="x")
    with pytest.raises(BizException) as e:
        service.create_after_sale(env, 1, body)
    assert e.value.code == 1403


def test_create_after_sale_wrong_status(env: FakeDb) -> None:
    body = CreateAfterSaleRequest(order_id=2, type="refund", reason="x")
    with pytest.raises(BizException) as e:
        service.create_after_sale(env, 1, body)
    assert e.value.code == 1402


def test_create_after_sale_duplicate(env: FakeDb) -> None:
    db = env
    db._after_sales[100] = _after_sale(100, order_id=1, status="applying")
    body = CreateAfterSaleRequest(order_id=1, type="refund", reason="x")
    with pytest.raises(BizException) as e:
        service.create_after_sale(db, 1, body)
    assert e.value.code == 1606


# ---- B5-14b 售后单列表/详情 ----

def test_list_after_sales_ok(env: FakeDb) -> None:
    db = env
    db._after_sales[100] = _after_sale(100, order_id=1)
    db._after_sales[101] = _after_sale(101, order_id=1, status="refunded")
    data = service.list_after_sales(db, 1, None, 1, 10)
    assert data.total == 2
    assert data.items[0].id == 101
    assert data.items[0].status_text == "已退款"


def test_list_after_sales_filter_status(env: FakeDb) -> None:
    db = env
    db._after_sales[100] = _after_sale(100, order_id=1)
    db._after_sales[101] = _after_sale(101, order_id=1, status="refunded")
    data = service.list_after_sales(db, 1, "refunded", 1, 10)
    assert data.total == 1
    assert data.items[0].id == 101


def test_get_after_sale_ok(env: FakeDb) -> None:
    db = env
    db._after_sales[100] = _after_sale(100, order_id=1)
    item = service.get_after_sale(db, 1, 100)
    assert item.id == 100
    assert item.reason == "商品破损"


def test_get_after_sale_not_found(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.get_after_sale(env, 1, 999)
    assert e.value.code == 404


def test_get_after_sale_not_owned(env: FakeDb) -> None:
    db = env
    db._after_sales[100] = _after_sale(100, order_id=1, user_id=2)
    with pytest.raises(BizException) as e:
        service.get_after_sale(db, 1, 100)
    assert e.value.code == 1403
