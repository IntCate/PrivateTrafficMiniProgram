"""收藏模块单元测试：列表、添加（幂等/下架拦截）、取消（幂等）。

对齐 docs/test-cases.md B6。使用内存 Fake 仓储/桩验证 service 业务分支（模式同 test_order.py）。
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.favorite import service
from app.modules.favorite.models import Favorite


def _product(
    id: int, *, name: str = "潮流运动鞋", price: str = "299.00", status: int = 1
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id, name=name, price=Decimal(price), status=status, main_image="/img.jpg"
    )


def _fav(id: int, product_id: int, *, user_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(id=id, user_id=user_id, product_id=product_id)


class FakeDb:
    """内存 Session：支持 add/commit，收藏行与商品桩按容器维护。"""

    def __init__(
        self,
        products: dict[int, SimpleNamespace],
        favorites: dict[int, SimpleNamespace] | None = None,
    ) -> None:
        self._products = products
        self._favorites: dict[int, SimpleNamespace] = favorites or {}
        self._next_id = 500
        self.commits = 0

    def add(self, obj: object) -> None:
        if isinstance(obj, Favorite):
            obj.id = self._next_id
            self._next_id += 1
            self._favorites[obj.id] = obj

    def commit(self) -> None:
        self.commits += 1


class FakeFavoriteRepo:
    """内存收藏仓储（替代 service 引用的 FavoriteRepository）。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db

    def list_by_user(
        self, user_id: int, page: int, page_size: int
    ) -> tuple[list[SimpleNamespace], int]:
        rows = sorted(
            (f for f in self.db._favorites.values() if f.user_id == user_id),
            key=lambda f: f.id,
            reverse=True,
        )
        total = len(rows)
        start = (page - 1) * page_size
        return rows[start : start + page_size], total

    def get_by_user_product(self, user_id: int, product_id: int) -> SimpleNamespace | None:
        for f in self.db._favorites.values():
            if f.user_id == user_id and f.product_id == product_id:
                return f
        return None

    def remove_by_product(self, user_id: int, product_id: int) -> int:
        before = len(self.db._favorites)
        self.db._favorites = {
            fid: f
            for fid, f in self.db._favorites.items()
            if not (f.user_id == user_id and f.product_id == product_id)
        }
        return before - len(self.db._favorites)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> tuple[FakeDb, dict[int, SimpleNamespace]]:
    db = FakeDb(
        products={
            1: _product(1),
            2: _product(2, name="简约单肩包", price="129.00"),
            3: _product(3, name="云朵抱枕靠垫", status=0),  # 下架
            4: _product(4, name="清新纯棉T恤", price="79.00"),
        },
        favorites={501: _fav(501, 1), 502: _fav(502, 2)},
    )

    monkeypatch.setattr(service, "FavoriteRepository", lambda d: FakeFavoriteRepo(d))
    monkeypatch.setattr(
        service, "_get_product", lambda d, pid: d._products.get(pid)
    )
    monkeypatch.setattr(
        service,
        "_list_products_by_ids",
        lambda d, ids: {i: d._products[i] for i in ids if i in d._products},
    )
    return db, db._products


# ---- B6-1 收藏/幂等 ----

def test_add_favorite_ok(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    data = service.add_favorite(db, 1, 1)
    assert data.favorited is True
    assert data.existed is True  # 种子已收藏 → 幂等返回 existed


def test_add_favorite_new_and_idempotent(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    first = service.add_favorite(db, 1, 4)
    assert first.favorited is True
    assert first.existed is False
    assert len(db._favorites) == 3
    second = service.add_favorite(db, 1, 4)
    assert second.existed is True
    assert len(db._favorites) == 3  # 不新增重复记录


# ---- B6-2 收藏下架商品 ----

def test_add_favorite_offshelf(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    with pytest.raises(BizException) as e:
        service.add_favorite(db, 1, 3)
    assert e.value.code == 1102


def test_add_favorite_not_found(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    with pytest.raises(BizException) as e:
        service.add_favorite(db, 1, 999)
    assert e.value.code == 404


# ---- 收藏列表 ----

def test_list_favorites_empty(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    db._favorites = {}
    data = service.list_favorites(db, 1, 1, 10)
    assert data.items == []
    assert data.total == 0
    assert data.has_more is False


def test_list_favorites_ok(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    data = service.list_favorites(db, 1, 1, 10)
    assert data.total == 2
    assert data.has_more is False
    assert [i.product_id for i in data.items] == [2, 1]  # 新收藏在前
    assert data.items[0].name == "简约单肩包"
    assert data.items[0].price == 129.0
    assert data.items[0].image == "/img.jpg"


def test_list_favorites_paginated(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    page1 = service.list_favorites(db, 1, 1, 1)
    assert len(page1.items) == 1
    assert page1.has_more is True
    page2 = service.list_favorites(db, 1, 2, 1)
    assert len(page2.items) == 1
    assert page2.has_more is False


# ---- B6-3 取消收藏 ----

def test_remove_favorite_ok(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    data = service.remove_favorite(db, 1, 1)
    assert data.favorited is False
    assert db._favorites.get(501) is None
    assert len(db._favorites) == 1


def test_remove_favorite_idempotent(env: tuple[FakeDb, dict]) -> None:
    db, _ = env
    data = service.remove_favorite(db, 1, 999)  # 未收藏
    assert data.favorited is False
    assert len(db._favorites) == 2  # 不报错、不影响已有收藏
