"""商品模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from typing import Any

from app.common.schemas import CamelModel


class CategoryOut(CamelModel):
    """分类对外信息。"""

    id: int
    name: str
    sort: int = 0


class ProductItemOut(CamelModel):
    """商品列表项。"""

    id: int
    product_no: str
    name: str
    sub_title: str | None = None
    price: float
    original_price: float | None = None
    main_image: str
    sales: int = 0
    tags: list[str] = []


class ProductSkuOut(CamelModel):
    """商品 SKU 对外信息。"""

    id: int
    attrs: list[dict[str, Any]] = []
    sku_text: str
    price: float
    stock: int = 0
    image: str | None = None


class ProductDetailOut(CamelModel):
    """商品详情。"""

    id: int
    product_no: str
    category_id: int
    name: str
    sub_title: str | None = None
    price: float
    original_price: float | None = None
    main_image: str
    images: list[str] = []
    detail_html: str | None = None
    spec: dict[str, Any] = {}
    sales: int = 0
    shipping_from: str | None = None
    is_free_shipping: bool = True
    tags: list[str] = []
    skus: list[ProductSkuOut] = []
    promises: list[str] = []


class BannerOut(CamelModel):
    """首页运营位。"""

    id: int
    title: str
    tag: str | None = None
    image: str
    link_type: str = "none"
    link_value: str | None = None


class HomeThemeOut(CamelModel):
    """首页主题精选。"""

    id: int
    name: str
    desc: str | None = None
    image: str
    link_type: str = "none"
    link_value: str | None = None


class HomeMemberOut(CamelModel):
    """首页会员聚合卡。"""

    points: int = 0
    coupon_count: int = 0
    nickname: str | None = None


class HomeIndexOut(CamelModel):
    """首页聚合出参。"""

    member: HomeMemberOut | None = None
    banners: list[BannerOut] = []
    themes: list[HomeThemeOut] = []
    promises: list[str] = []
