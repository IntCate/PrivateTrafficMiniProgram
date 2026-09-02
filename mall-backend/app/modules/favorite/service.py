"""收藏模块业务逻辑。对齐 docs/api-design.md §10 与 mock store.js。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.favorite.models import Favorite
from app.modules.favorite.repository import FavoriteRepository
from app.modules.favorite.schemas import FavoriteActionOut, FavoriteItemOut, FavoriteListOut
from app.modules.product.models import PRODUCT_STATUS_ON, Product


def _get_product(db: Session, product_id: int) -> Product | None:
    """按 ID 查询商品。"""
    return db.scalar(select(Product).where(Product.id == product_id))


def _list_products_by_ids(db: Session, product_ids: list[int]) -> dict[int, Product]:
    """批量按 ID 查询商品，返回 {id: Product}。"""
    if not product_ids:
        return {}
    rows = db.scalars(select(Product).where(Product.id.in_(product_ids)))
    return {p.id: p for p in rows}


def list_favorites(
    db: Session, user_id: int, page: int, page_size: int
) -> FavoriteListOut:
    """收藏列表（对齐 api-design §10.1，列表不拦截下架商品，对齐 mock）。"""
    repo = FavoriteRepository(db)
    rows, total = repo.list_by_user(user_id, page, page_size)
    items = _build_items(db, rows)
    return FavoriteListOut(
        items=items, total=total, page=page, page_size=page_size, has_more=page * page_size < total
    )


def add_favorite(db: Session, user_id: int, product_id: int) -> FavoriteActionOut:
    """添加收藏（对齐 api-design §10.2）。

    - 商品不存在：404（对齐 cart 风格，mock 对不存在商品同样拦截）
    - 商品下架：1102「商品已下架」（对齐 test-cases B6-2）
    - 已收藏：幂等返回 existed=true，不新增（对齐 B6-1）
    """
    product = _get_product(db, product_id)
    if product is None:
        raise BizException(404, "商品不存在")
    if product.status != PRODUCT_STATUS_ON:
        raise BizException(1102, "商品已下架")

    repo = FavoriteRepository(db)
    if repo.get_by_user_product(user_id, product_id) is not None:
        return FavoriteActionOut(favorited=True, existed=True)

    db.add(Favorite(user_id=user_id, product_id=product_id))
    db.commit()
    return FavoriteActionOut(favorited=True, existed=False)


def remove_favorite(db: Session, user_id: int, product_id: int) -> FavoriteActionOut:
    """取消收藏（对齐 api-design §10.3，幂等移除，对齐 B6-3）。"""
    FavoriteRepository(db).remove_by_product(user_id, product_id)
    db.commit()
    return FavoriteActionOut(favorited=False)


def _build_items(db: Session, rows: list[Favorite]) -> list[FavoriteItemOut]:
    """按收藏行批量回读商品信息组装列表项（对齐 mock listFavorites）。"""
    if not rows:
        return []
    products = _list_products_by_ids(db, [row.product_id for row in rows])
    return [
        FavoriteItemOut(
            id=row.id,
            product_id=row.product_id,
            name=products[row.product_id].name if row.product_id in products else "",
            price=float(products[row.product_id].price)
            if row.product_id in products
            else 0.0,
            image=products[row.product_id].main_image if row.product_id in products else "",
        )
        for row in rows
    ]
