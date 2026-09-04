"""优惠券模块单元测试：领取、列表、核销校验。

对齐 docs/test-cases.md B8（优惠券）。使用内存 Fake 仓储/桩验证 service 业务分支。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.coupon import service
from app.modules.coupon.models import Coupon, UserCoupon


def _coupon(
    id: int,
    *,
    name: str = "满100减20",
    type: str = "cash",
    amount: str | None = "20.00",
    discount: str | None = None,
    min_amount: str = "100.00",
    total_count: int = 0,
    received_count: int = 0,
    status: int = 1,
    valid_start: datetime | None = None,
    valid_end: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        name=name,
        type=type,
        amount=Decimal(amount) if amount else None,
        discount=Decimal(discount) if discount else None,
        min_amount=Decimal(min_amount),
        total_count=total_count,
        received_count=received_count,
        status=status,
        valid_start=valid_start,
        valid_end=valid_end,
    )


def _user_coupon(
    id: int,
    *,
    user_id: int = 1,
    coupon_id: int = 1,
    status: str = "unused",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        user_id=user_id,
        coupon_id=coupon_id,
        status=status,
        used_order_no=None,
        used_at=None,
    )


class FakeDb:
    """内存 Session：支持 get(Coupon/UserCoupon) 与 add/flush/commit。"""

    def __init__(
        self,
        coupons: dict[int, SimpleNamespace],
        user_coupons: dict[int, SimpleNamespace] | None = None,
    ) -> None:
        self._coupons = coupons
        self._user_coupons: dict[int, SimpleNamespace] = user_coupons or {}
        self._pending: list[object] = []
        self._next_uc_id = 100
        self.commits = 0

    def get(self, model: type, pk: int) -> object | None:
        if model is Coupon:
            return self._coupons.get(pk)
        if model is UserCoupon:
            return self._user_coupons.get(pk)
        return None

    def scalars(self, stmt: object) -> list[SimpleNamespace]:
        return list(self._coupons.values())
    def add(self, obj: object) -> None:
        self._pending.append(obj)

    def flush(self) -> None:
        for obj in self._pending:
            if isinstance(obj, UserCoupon):
                obj.id = self._next_uc_id
                self._next_uc_id += 1
                self._user_coupons[obj.id] = obj
        self._pending = []

    def commit(self) -> None:
        self.commits += 1


class FakeUserCouponRepo:
    """内存用户券仓储。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db

    def get_by_user_coupon(self, user_id: int, coupon_id: int) -> SimpleNamespace | None:
        for uc in self.db._user_coupons.values():
            if uc.user_id == user_id and uc.coupon_id == coupon_id:
                return uc
        return None

    def list_by_user(
        self, user_id: int, status: str | None, page: int, page_size: int
    ) -> tuple[list[SimpleNamespace], int]:
        rows = [uc for uc in self.db._user_coupons.values() if uc.user_id == user_id]
        if status:
            rows = [uc for uc in rows if uc.status == status]
        rows.sort(key=lambda uc: uc.id, reverse=True)
        total = len(rows)
        start = (page - 1) * page_size
        return rows[start : start + page_size], total

    def count_unused(self, user_id: int) -> int:
        return sum(
            1
            for uc in self.db._user_coupons.values()
            if uc.user_id == user_id and uc.status == "unused"
        )


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> FakeDb:
    now = datetime.now()
    db = FakeDb(
        coupons={
            1: _coupon(1),
            2: _coupon(2, name="8折券", type="discount", amount=None, discount="0.80"),
            3: _coupon(3, name="已停用", status=0),
            4: _coupon(4, name="已过期", valid_end=now - timedelta(days=1)),
            5: _coupon(5, name="未生效", valid_start=now + timedelta(days=1)),
            6: _coupon(6, name="已领完", total_count=1, received_count=1),
        },
        user_coupons={},
    )
    monkeypatch.setattr(service, "UserCouponRepository", lambda d: FakeUserCouponRepo(d))
    return db


# ---- B8-1 领取优惠券 ----

def test_receive_coupon_ok(env: FakeDb) -> None:
    db = env
    result = service.receive_coupon(db, 1, 1)
    assert result.existed is False
    assert result.user_coupon_id == 100
    assert db._coupons[1].received_count == 1
    assert db._user_coupons[100].status == "unused"


def test_receive_coupon_not_found(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.receive_coupon(env, 1, 999)
    assert e.value.code == 1601


def test_receive_coupon_already_received(env: FakeDb) -> None:
    db = env
    db._user_coupons[100] = _user_coupon(100, user_id=1, coupon_id=1)
    result = service.receive_coupon(db, 1, 1)
    assert result.existed is True


def test_receive_coupon_disabled(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.receive_coupon(env, 1, 3)
    assert e.value.code == 1603


def test_receive_coupon_expired(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.receive_coupon(env, 1, 4)
    assert e.value.code == 1603


def test_receive_coupon_not_started(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.receive_coupon(env, 1, 5)
    assert e.value.code == 1603


def test_receive_coupon_sold_out(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.receive_coupon(env, 1, 6)
    assert e.value.code == 1603


# ---- B8-2 优惠券列表 ----

def test_list_coupons_ok(env: FakeDb) -> None:
    db = env
    db._user_coupons[100] = _user_coupon(100, user_id=1, coupon_id=1)
    db._user_coupons[101] = _user_coupon(101, user_id=1, coupon_id=2)
    data = service.list_coupons(db, 1, None, 1, 10)
    assert data.total == 2
    assert data.items[0].name == "8折券"
    assert data.items[0].discount == 0.8


def test_list_coupons_filter_status(env: FakeDb) -> None:
    db = env
    db._user_coupons[100] = _user_coupon(100, user_id=1, coupon_id=1)
    db._user_coupons[101] = _user_coupon(101, user_id=1, coupon_id=2, status="used")
    data = service.list_coupons(db, 1, "used", 1, 10)
    assert data.total == 1
    assert data.items[0].coupon_id == 2
