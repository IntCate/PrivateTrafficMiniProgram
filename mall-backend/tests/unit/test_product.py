"""商品模块单元测试：列表过滤、详情下架/不存在、首页聚合。"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.product import service


def _product(id: int, *, status: int = 1, deleted: bool = False) -> object:
    return SimpleNamespace(
        id=id,
        product_no=f"P{id}",
        category_id=1,
        name=f"商品{id}",
        sub_title="副标题",
        price=99.0,
        original_price=199.0,
        main_image="/img.jpg",
        images=["/img.jpg"],
        detail_html="<p>d</p>",
        spec={"材质": "棉"},
        sales=10,
        shipping_from="上海",
        is_free_shipping=True,
        tags=["热销"],
        status=status,
        deleted=deleted,
    )


def test_get_product_detail_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeRepo:
        def get(self, pid: int) -> object:
            return _product(pid)

    class FakeSkuRepo:
        def list_by_product(self, pid: int) -> list[object]:
            return [
                SimpleNamespace(
                    id=1,
                    attrs=[{"name": "颜色", "value": "白"}],
                    sku_text="白；均码",
                    price=99.0,
                    stock=5,
                    image=None,
                )
            ]

    monkeypatch.setattr(service.ProductRepository, "__init__", lambda *a, **k: None)
    monkeypatch.setattr(service.ProductRepository, "get", FakeRepo().get)
    monkeypatch.setattr(service.ProductSkuRepository, "__init__", lambda *a, **k: None)
    monkeypatch.setattr(
        service.ProductSkuRepository, "list_by_product", FakeSkuRepo().list_by_product
    )

    result = service.get_product_detail(_db(), 1)
    assert result["id"] == 1
    assert result["skus"][0]["sku_text"] == "白；均码"
    assert result["promises"] == service.PROMISES


def test_get_product_detail_off_sale(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(self, pid: int) -> object:
        return _product(pid, status=0)

    monkeypatch.setattr(service.ProductRepository, "__init__", lambda *a, **k: None)
    monkeypatch.setattr(service.ProductRepository, "get", fake_get)
    with pytest.raises(BizException) as exc:
        service.get_product_detail(_db(), 10)
    assert exc.value.code == 1102


def test_get_product_detail_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(self, pid: int) -> None:
        return None

    monkeypatch.setattr(service.ProductRepository, "__init__", lambda *a, **k: None)
    monkeypatch.setattr(service.ProductRepository, "get", fake_get)
    with pytest.raises(BizException) as exc:
        service.get_product_detail(_db(), 999)
    assert exc.value.code == 404


def test_home_index_anon_and_logged() -> None:
    class FakeBannerRepo:
        def __init__(self, db: object) -> None:
            self.db = db

        def list_by(self, **kwargs: object) -> list[object]:
            return [
                SimpleNamespace(
                    id=1,
                    title="标题",
                    sub_title="标签",
                    image="/img.jpg",
                    link_type="page",
                    link_value="/pages/x",
                    sort=1,
                )
            ]

    import app.modules.product.service as svc

    orig = svc.BannerRepository
    svc.BannerRepository = FakeBannerRepo  # type: ignore[misc]
    try:
        anon = service.home_index(_db(), member=None)
        assert anon["member"] is None
        assert anon["banners"][0]["link_value"] == "/pages/x"
        assert anon["promises"] == svc.PROMISES

        member = SimpleNamespace(points=10, coupon_count=0, nickname="张三")
        logged = service.home_index(_db(), member=member)
        assert logged["member"]["points"] == 10
        assert logged["member"]["nickname"] == "张三"
    finally:
        svc.BannerRepository = orig


def _db() -> object:
    """返回一个仅用于占位、不被查询使用的假 Session。"""
    return SimpleNamespace(scalar=lambda *a, **k: None)
