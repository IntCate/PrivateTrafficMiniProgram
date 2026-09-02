"""收藏模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from pydantic import Field

from app.common.schemas import CamelModel


class FavoriteItemOut(CamelModel):
    """收藏列表项（对齐 api-design §10.1）。"""

    id: int
    product_id: int
    name: str
    price: float
    image: str | None = None


class FavoriteListOut(CamelModel):
    """收藏列表分页（对齐 api-design §10.1）。"""

    items: list[FavoriteItemOut] = Field(default_factory=list, serialization_alias="list")
    total: int
    page: int
    page_size: int
    has_more: bool


class FavoriteActionOut(CamelModel):
    """收藏/取消收藏结果（对齐 api-design §10.2/§10.3 / mock store.js）。"""

    favorited: bool
    existed: bool | None = None
