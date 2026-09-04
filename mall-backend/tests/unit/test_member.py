"""会员中心模块单元测试：概览聚合、资料更新合法/非法。

对齐 docs/test-cases.md B7。使用内存 Fake 仓储/桩验证 service 业务分支（模式同 test_order.py）。
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.member import service
from app.modules.member.schemas import UpdateProfileRequest


def _member(**overrides: object) -> SimpleNamespace:
    base = dict(
        id=1,
        nickname="快乐购物家",
        avatar="",
        member_level="gold",
        points=10,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class FakeOrderRepo:
    """内存订单仓储（替代 service 引用的 OrderRepository）。"""

    def __init__(self, counts: dict[str, int]) -> None:
        self._counts = counts

    def stats_by_user(self, user_id: int) -> dict[str, int]:
        return self._counts


class FakeDb:
    """内存 Session：仅统计 commit 次数。"""

    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    counts = {"pending": 1, "paid": 0, "shipped": 2, "refund": 0}
    fake = FakeOrderRepo(counts)
    monkeypatch.setattr(service, "OrderRepository", lambda db: fake)

    class FakeUserCouponRepo:
        def __init__(self, db: object) -> None:
            pass

        def count_unused(self, user_id: int) -> int:
            return 0

    monkeypatch.setattr(service, "UserCouponRepository", FakeUserCouponRepo)
    return SimpleNamespace(counts=counts, member=_member())


# ---- B7-1 会员概览 ----

def test_overview_ok(env: SimpleNamespace) -> None:
    member = env.member
    data = service.get_overview(SimpleNamespace(), member)
    assert data.member.id == 1
    assert data.member.nickname == "快乐购物家"
    assert data.member.member_level == "gold"
    assert data.member.member_level_text == "黄金会员"
    assert data.member.points == 10
    assert data.member.coupon_count == 0  # 优惠券模块预留
    assert data.order_stats.pending == 1
    assert data.order_stats.shipped == 2
    assert data.order_stats.paid == 0
    assert data.order_stats.refund == 0


def test_overview_bronze_text(env: SimpleNamespace) -> None:
    member = _member(member_level="bronze")
    data = service.get_overview(SimpleNamespace(), member)
    assert data.member.member_level_text == "普通会员"


def test_overview_nickname_none_fallback(env: SimpleNamespace) -> None:
    member = _member(nickname=None, avatar=None)
    data = service.get_overview(SimpleNamespace(), member)
    assert data.member.nickname == ""
    assert data.member.avatar == ""


# ---- B7-2 资料更新合法 ----

def test_update_profile_ok(env: SimpleNamespace) -> None:
    member = env.member
    db = FakeDb()
    data = service.update_profile(
        db, member, UpdateProfileRequest(nickname="新昵称", avatar="https://cdn.example.com/a.jpg")
    )
    assert data.nickname == "新昵称"
    assert data.avatar == "https://cdn.example.com/a.jpg"
    assert member.nickname == "新昵称"
    assert member.avatar == "https://cdn.example.com/a.jpg"
    assert db.commits == 1


def test_update_profile_nickname_trimmed(env: SimpleNamespace) -> None:
    member = env.member
    data = service.update_profile(
        FakeDb(), member, UpdateProfileRequest(nickname="  新昵称  ")
    )
    assert data.nickname == "新昵称"
    assert data.avatar == ""  # 未传头像保留原值
    assert member.nickname == "新昵称"


# ---- B7-3 资料更新非法 ----

def test_update_profile_empty_nickname(env: SimpleNamespace) -> None:
    with pytest.raises(BizException) as e:
        service.update_profile(
            FakeDb(), env.member, UpdateProfileRequest(nickname="   ")
        )
    assert e.value.code == 1003


def test_update_profile_nickname_too_long(env: SimpleNamespace) -> None:
    with pytest.raises(BizException) as e:
        service.update_profile(
            FakeDb(), env.member, UpdateProfileRequest(nickname="长" * 21)
        )
    assert e.value.code == 1003


def test_update_profile_bad_avatar(env: SimpleNamespace) -> None:
    with pytest.raises(BizException) as e:
        service.update_profile(
            FakeDb(), env.member, UpdateProfileRequest(nickname="张三", avatar="not-a-url")
        )
    assert e.value.code == 1003


def test_update_profile_boundary_len20(env: SimpleNamespace) -> None:
    member = env.member
    data = service.update_profile(
        FakeDb(), member, UpdateProfileRequest(nickname="界" * 20)
    )
    assert data.nickname == "界" * 20
