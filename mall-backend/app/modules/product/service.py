"""商品模块业务逻辑：分类、商品列表/详情、首页聚合。"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.product.models import BANNER_POS_HERO, BANNER_POS_THEME, PRODUCT_STATUS_ON
from app.modules.product.repository import (
    BannerRepository,
    CategoryRepository,
    ProductRepository,
    ProductSkuRepository,
)

logger = logging.getLogger("app.modules.product.service")

# 品牌承诺（对齐 api-design §4.1 与前端 mock）
PROMISES: list[str] = ["正品保障", "7天无理由", "极速发货"]


def list_categories(db: Session) -> list[dict[str, Any]]:
    """分类列表：返回启用分类，按 sort 升序。"""
    repo = CategoryRepository(db)
    rows = repo.list_by(status=1)
    rows.sort(key=lambda c: c.sort)
    return [
        {
            "id": c.id,
            "name": c.name,
            "sort": c.sort,
        }
        for c in rows
    ]


def list_products(
    db: Session,
    *,
    category_id: int | None = None,
    keyword: str | None = None,
    sort: str = "default",
    order: str = "desc",
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """商品列表（公开）：过滤下架、分页、排序、关键词搜索。"""
    repo = ProductRepository(db)
    rows, total = repo.list_on_sale(
        category_id=category_id,
        keyword=keyword,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    list_items: list[dict[str, Any]] = []
    for p in rows:
        list_items.append(
            {
                "id": p.id,
                "product_no": p.product_no,
                "name": p.name,
                "sub_title": p.sub_title,
                "price": p.price,
                "original_price": p.original_price,
                "main_image": p.main_image,
                "sales": p.sales,
                "tags": _as_list(p.tags),
            }
        )
    return {
        "list": list_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": page * page_size < total,
    }


def get_product_detail(db: Session, product_id: int) -> dict[str, Any]:
    """商品详情：下架返回 1102，不存在返回 404。"""
    repo = ProductRepository(db)
    product = repo.get(product_id)
    if not product or product.deleted:
        raise BizException(404, "商品不存在")

    if product.status != PRODUCT_STATUS_ON:
        raise BizException(1102, "商品已下架")

    sku_repo = ProductSkuRepository(db)
    skus = sku_repo.list_by_product(product_id)

    return {
        "id": product.id,
        "product_no": product.product_no,
        "category_id": product.category_id,
        "name": product.name,
        "sub_title": product.sub_title,
        "price": product.price,
        "original_price": product.original_price,
        "main_image": product.main_image,
        "images": _as_list(product.images),
        "detail_html": product.detail_html,
        "spec": _as_dict(product.spec),
        "sales": product.sales,
        "shipping_from": product.shipping_from,
        "is_free_shipping": bool(product.is_free_shipping),
        "tags": _as_list(product.tags),
        "skus": [
            {
                "id": s.id,
                "attrs": _as_list(s.attrs),
                "sku_text": s.sku_text,
                "price": s.price,
                "stock": s.stock,
                "image": s.image,
            }
            for s in skus
        ],
        "promises": PROMISES,
    }


def home_index(db: Session, member: Any | None = None) -> dict[str, Any]:
    """首页聚合：会员卡 + 主横幅 + 主题精选 + 品牌承诺。"""
    banner_repo = BannerRepository(db)
    banners = banner_repo.list_by(position=BANNER_POS_HERO, status=1)
    themes = banner_repo.list_by(position=BANNER_POS_THEME, status=1)
    banners.sort(key=lambda b: b.sort)
    themes.sort(key=lambda b: b.sort)

    member_out = None
    if member is not None:
        member_out = {
            "points": member.points,
            "coupon_count": 0,
            "nickname": member.nickname,
        }

    return {
        "member": member_out,
        "banners": [
            {
                "id": b.id,
                "title": b.title,
                "tag": b.sub_title,
                "image": b.image,
                "link_type": b.link_type,
                "link_value": b.link_value,
            }
            for b in banners
        ],
        "themes": [
            {
                "id": b.id,
                "name": b.title,
                "desc": b.sub_title,
                "image": b.image,
                "link_type": b.link_type,
                "link_value": b.link_value,
            }
            for b in themes
        ],
        "promises": PROMISES,
    }


def _as_list(value: Any) -> list[Any]:
    """JSON 字段安全转列表。"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _as_dict(value: Any) -> dict[str, Any]:
    """JSON 字段安全转字典。"""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {}
