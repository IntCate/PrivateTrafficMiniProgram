"""商品模块路由（公开）：首页聚合、分类列表、商品列表/详情。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import get_bearer_token
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import PageResult, ok
from app.modules.product import service
from app.modules.product.schemas import (
    CategoryOut,
    HomeIndexOut,
    ProductDetailOut,
    ProductItemOut,
)

product_router = APIRouter(prefix="/products", tags=["product"])
home_router = APIRouter(prefix="/home", tags=["home"])
category_router = APIRouter(prefix="/categories", tags=["category"])


def _optional_member(
    token: str | None = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> object | None:
    """首页可选登录：有有效 token 返回会员，否则返回 None（不阻拦公开访问）。"""
    if not token:
        return None
    from app.common.deps import get_current_member

    try:
        return get_current_member(token=token, db=db)
    except BizException:
        return None


@home_router.get("/index")
def do_home_index(
    db: Session = Depends(get_db),
    member: object = Depends(_optional_member),
) -> dict:
    """首页聚合（公开）：未登录 member 为 null。"""
    data = service.home_index(db, member)
    return ok(HomeIndexOut.model_validate(data).model_dump(by_alias=True))


@category_router.get("")
def do_list_categories(db: Session = Depends(get_db)) -> dict:
    """分类列表（公开）。"""
    rows = service.list_categories(db)
    return ok({"list": [CategoryOut.model_validate(r).model_dump(by_alias=True) for r in rows]})


@product_router.get("")
def do_list_products(
    db: Session = Depends(get_db),
    category_id: int | None = Query(default=None, alias="categoryId"),
    keyword: str | None = Query(default=None, max_length=50),
    sort: str = Query(default="default"),
    order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50, alias="pageSize"),
) -> dict:
    """商品列表（公开）：过滤下架、分页、排序、搜索。"""
    data = service.list_products(
        db,
        category_id=category_id,
        keyword=keyword,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    items = [
        ProductItemOut.model_validate(r).model_dump(by_alias=True) for r in data["list"]
    ]
    result: PageResult[dict[str, object]] = PageResult(
        list=items,
        total=data["total"],
        page=data["page"],
        pageSize=data["page_size"],
        hasMore=data["has_more"],
    )
    return ok(result.model_dump())


@product_router.get("/{product_id}")
def do_get_product(product_id: int, db: Session = Depends(get_db)) -> dict:
    """商品详情（公开）：下架 1102，不存在 404。"""
    data = service.get_product_detail(db, product_id)
    return ok(ProductDetailOut.model_validate(data).model_dump(by_alias=True))
