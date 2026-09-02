"""购物车模块单元测试：列表合计、加购、改项、删除、全选。

对齐 docs/test-cases.md B3。使用内存 Fake 仓储验证 service 业务分支。
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.cart import service
from app.modules.cart.models import CART_QUANTITY_MAX
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
    selected: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        user_id=user_id,
        product_id=product_id,
        sku_id=sku_id,
        quantity=quantity,
        selected=selected,
    )


class FakeDb:
    """内存 Session：仅支持 get(Product/ProductSku) 与 commit。"""

    def __init__(
        self, skus: dict[int, SimpleNamespace], products: dict[int, SimpleNamespace]
    ) -> None:
        self._skus = skus
        self._products = products
        self.commits = 0

    def get(self, model: type, pk: int) -> object | None:
        if model is ProductSku:
            return self._skus.get(pk)
        if model is Product:
            return self._products.get(pk)
        return None

    def commit(self) -> None:
        self.commits += 1


class FakeCartRepo:
    """内存购物车仓储：基于列表模拟全部仓储方法。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db
        self.rows: list[SimpleNamespace] = []
        self._next_id = 1

    def list_by_user(self, user_id: int) -> list[SimpleNamespace]:
        return [r for r in self.rows if r.user_id == user_id]

    def get_owned(self, user_id: int, item_id: int) -> SimpleNamespace | None:
        return next((r for r in self.rows if r.id == item_id and r.user_id == user_id), None)

    def get_by_user_sku(self, user_id: int, sku_id: int) -> SimpleNamespace | None:
        return next((r for r in self.rows if r.user_id == user_id and r.sku_id == sku_id), None)

    def save(self, obj: SimpleNamespace) -> SimpleNamespace:
        if getattr(obj, "id", 0):
            for i, r in enumerate(self.rows):
                if r.id == obj.id:
                    self.rows[i] = obj
                    return obj
        obj.id = self._next_id
        self._next_id += 1
        self.rows.append(obj)
        return obj

    def delete(self, obj: SimpleNamespace) -> None:
        self.rows = [r for r in self.rows if r.id != obj.id]

    def delete_owned(self, user_id: int, ids: list[int]) -> int:
        before = len(self.rows)
        self.rows = [r for r in self.rows if not (r.user_id == user_id and r.id in ids)]
        return before - len(self.rows)

    def set_all_selected(self, user_id: int, selected: bool) -> None:
        for r in self.rows:
            if r.user_id == user_id:
                r.selected = selected

    def set_select_where(self, user_id: int, ids: list[int], selected: bool) -> None:
        for r in self.rows:
            if r.user_id == user_id and r.id in ids:
                r.selected = selected


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> tuple[FakeDb, FakeCartRepo]:
    db = FakeDb(
        skus={
            10: _sku(10),
            11: _sku(11, product_id=1, sku_text="黑；41"),
            20: _sku(20, product_id=2),
        },
        products={1: _product(1), 2: _product(2, name="帆布鞋")},
    )
    repo = FakeCartRepo(db)
    # service 内部每次 CartRepository(db) 都返回同一个内存 repo，保证状态跨调用共享
    monkeypatch.setattr(service, "CartRepository", lambda d: repo)  # type: ignore[misc]
    monkeypatch.setattr(
        service,
        "_load_skus",
        lambda d, ids: {i: db._skus[i] for i in ids if i in db._skus},
    )
    monkeypatch.setattr(
        service,
        "_load_products",
        lambda d, ids: {i: db._products[i] for i in ids if i in db._products},
    )
    return db, repo


def test_get_cart_empty(env: tuple[FakeDb, FakeCartRepo]) -> None:
    _, repo = env
    repo.rows = []
    state = service.get_cart(FakeDb({}, {}), 1)
    assert state["list"] == []
    assert state["totalPrice"] == 0.0
    assert state["totalQuantity"] == 0


def test_get_cart_totals_only_saleable_selected(env: tuple[FakeDb, FakeCartRepo]) -> None:
    _, repo = env
    repo.rows = [
        _cart(1, sku_id=10, quantity=2, selected=True),  # 可售勾选：100*2
        _cart(2, sku_id=11, quantity=3, selected=False),  # 可售未勾选：不计
    ]
    state = service.get_cart(env[0], 1)
    assert len(state["list"]) == 2
    assert state["totalPrice"] == 200.0
    assert state["totalQuantity"] == 2


def test_get_cart_off_sale_kept_and_excluded(env: tuple[FakeDb, FakeCartRepo]) -> None:
    env[0]._skus[10] = _sku(10, status=0)
    _, repo = env
    repo.rows = [_cart(1, sku_id=10, quantity=2, selected=True)]
    state = service.get_cart(env[0], 1)
    assert state["list"][0]["onSale"] is False
    assert state["totalPrice"] == 0.0
    assert state["totalQuantity"] == 0


def test_add_item_new(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    state = service.add_item(db, 1, 10, quantity=1)
    assert len(state["list"]) == 1
    assert state["list"][0]["skuId"] == 10
    assert state["list"][0]["selected"] is False  # 新增默认不勾选
    assert state["list"][0]["stock"] == 50


def test_add_item_merge_same_sku(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    repo.rows = [_cart(1, sku_id=10, quantity=2)]
    state = service.add_item(db, 1, 10, quantity=3)
    assert len(state["list"]) == 1
    assert state["list"][0]["quantity"] == 5


def test_add_item_exceeds_limit(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.add_item(db, 1, 10, quantity=CART_QUANTITY_MAX + 1)
    assert exc.value.code == 1201
    assert exc.value.data == {"maxQuantity": CART_QUANTITY_MAX}


def test_add_item_out_of_stock(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.add_item(db, 1, 10, quantity=60)
    assert exc.value.code == 1104
    assert exc.value.data == {"availableStock": 50}


def test_add_item_off_sale(env: tuple[FakeDb, FakeCartRepo]) -> None:
    env[0]._products[1] = _product(1, status=0)
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.add_item(db, 1, 10)
    assert exc.value.code == 1102


def test_update_item_quantity(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    repo.rows = [_cart(1, sku_id=10, quantity=1)]
    state = service.update_item(db, 1, 1, quantity=5)
    assert state["list"][0]["quantity"] == 5


def test_update_item_quantity_zero_deletes(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    repo.rows = [_cart(1, sku_id=10, quantity=1)]
    state = service.update_item(db, 1, 1, quantity=0)
    assert state["list"] == []


def test_update_item_not_found(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.update_item(db, 1, 999, quantity=2)
    assert exc.value.code == 404


def test_update_item_cross_product_sku(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    repo.rows = [_cart(1, sku_id=10)]
    with pytest.raises(BizException) as exc:
        service.update_item(db, 1, 1, sku_id=20)  # SKU 20 属于商品 2
    assert exc.value.code == 400


def test_update_item_switch_sku(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    repo.rows = [_cart(1, sku_id=10)]
    state = service.update_item(db, 1, 1, sku_id=11)
    assert state["list"][0]["skuId"] == 11
    assert state["list"][0]["skuText"] == "黑；41"


def test_delete_items_empty_ids(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.delete_items(db, 1, [])
    assert exc.value.code == 400


def test_delete_items(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    repo.rows = [_cart(1, sku_id=10), _cart(2, sku_id=11)]
    state = service.delete_items(db, 1, [1])
    assert [i["id"] for i in state["list"]] == [2]


def test_select_all_only_saleable(env: tuple[FakeDb, FakeCartRepo]) -> None:
    env[0]._skus[11] = _sku(11, status=0)  # SKU 11 停售 → 失效项
    db, repo = env
    repo.rows = [_cart(1, sku_id=10), _cart(2, sku_id=11)]
    state = service.select_all(db, 1, True)
    by_sku = {i["skuId"]: i["selected"] for i in state["list"]}
    assert by_sku[10] is True  # 可售项勾选
    assert by_sku[11] is False  # 失效项不参与全选


def test_select_all_cancel(env: tuple[FakeDb, FakeCartRepo]) -> None:
    db, repo = env
    repo.rows = [_cart(1, sku_id=10, selected=True), _cart(2, sku_id=11, selected=True)]
    state = service.select_all(db, 1, False)
    assert all(i["selected"] is False for i in state["list"])
