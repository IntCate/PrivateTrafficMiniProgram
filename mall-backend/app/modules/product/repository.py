"""商品模块数据访问。"""
from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select

from app.common.repository import BaseRepository
from app.modules.product.models import Banner, Category, Product, ProductSku

# 排序字段白名单：契约仅允许 default/sales/price
SORT_COLUMNS: dict[str, Any] = {
    "default": Product.id,
    "sales": Product.sales,
    "price": Product.price,
}


class CategoryRepository(BaseRepository[Category]):
    model = Category


class BannerRepository(BaseRepository[Banner]):
    model = Banner


class ProductRepository(BaseRepository[Product]):
    model = Product

    def list_on_sale(
        self,
        *,
        category_id: int | None = None,
        keyword: str | None = None,
        sort: str = "default",
        order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Product], int]:
        """分页查询上架商品（含分类/关键词过滤、排序）。

        下架商品不进列表（status=1 过滤），对齐 api-design §6.1 与 test-cases B2-3。
        """
        from app.modules.product.models import PRODUCT_STATUS_ON

        filters = [Product.status == PRODUCT_STATUS_ON, Product.deleted == False]  # noqa: E712
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        if keyword:
            like = f"%{keyword}%"
            filters.append(or_(Product.name.like(like), Product.sub_title.like(like)))

        count_stmt = select(func.count(Product.id)).where(*filters)
        total = self.db.scalar(count_stmt) or 0

        order_col = SORT_COLUMNS.get(sort, Product.id)
        order_expr = order_col.asc() if order == "asc" else order_col.desc()
        stmt = (
            select(Product)
            .where(*filters)
            .order_by(order_expr, Product.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(self.db.scalars(stmt))
        return rows, total


class ProductSkuRepository(BaseRepository[ProductSku]):
    model = ProductSku

    def list_by_product(self, product_id: int) -> list[ProductSku]:
        """查询某商品全部可售 SKU。"""
        from app.modules.product.models import PRODUCT_STATUS_ON

        stmt = (
            select(ProductSku)
            .where(
                ProductSku.product_id == product_id,
                ProductSku.status == PRODUCT_STATUS_ON,
                ProductSku.deleted == False,  # noqa: E712
            )
            .order_by(ProductSku.id.asc())
        )
        return list(self.db.scalars(stmt))
