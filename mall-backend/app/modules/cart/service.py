"""购物车模块业务逻辑：列表 / 加购 / 改项 / 删除 / 全选。

对齐 docs/api-design.md §7 与 docs/test-cases.md B3。
所有变更接口统一返回最新购物车状态 {list, totalPrice, totalQuantity}，
供前端 cart.vue syncCart 直接渲染。
"""
from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.cart.models import CART_QUANTITY_MAX, Cart
from app.modules.cart.repository import CartRepository
from app.modules.cart.schemas import CartItemOut, CartStateOut
from app.modules.product.models import Product, ProductSku

logger = logging.getLogger("app.modules.cart.service")


def _available_stock(sku: ProductSku) -> int:
    """可用库存 = 总库存 - 锁定库存。"""
    return max(sku.stock - sku.lock_stock, 0)


def _validate_quantity(quantity: int, available: int) -> int:
    """数量校验（对齐 api-design §7.2 / test-cases B3-4/B3-5）。

    - 超出单次限购 → 1201（data.maxQuantity）
    - 超出可用库存 → 1104（data.availableStock）
    """
    if quantity < 1:
        raise BizException(400, "数量不能小于 1")
    if quantity > CART_QUANTITY_MAX:
        raise BizException(
            1201,
            f"单次限购 {CART_QUANTITY_MAX} 件",
            {"maxQuantity": CART_QUANTITY_MAX},
        )
    if quantity > available:
        raise BizException(1104, "库存不足", {"availableStock": available})
    return quantity


def _get_saleable_sku(db: Session, sku_id: int) -> tuple[Product, ProductSku]:
    """加载 SKU 与其商品，校验存在性与可售性。

    - 不存在 → 404
    - 商品下架 / SKU 停售 → 1102（购物车仅保留既有下架项，不允许新增不可售 SKU）
    """
    sku = db.get(ProductSku, sku_id)
    if sku is None or sku.deleted:
        raise BizException(404, "SKU 不存在")
    product = db.get(Product, sku.product_id)
    if product is None or product.deleted:
        raise BizException(404, "商品不存在")
    if product.status != 1 or sku.status != 1:
        raise BizException(1102, "商品已下架")
    return product, sku


def _load_products(db: Session, ids: set[int]) -> dict[int, Product]:
    """批量加载商品（dict[id, Product]）。"""
    return {
        p.id: p for p in db.scalars(select(Product).where(Product.id.in_(ids)))
    }


def _load_skus(db: Session, ids: set[int]) -> dict[int, ProductSku]:
    """批量加载 SKU（dict[id, ProductSku]）。"""
    return {
        s.id: s for s in db.scalars(select(ProductSku).where(ProductSku.id.in_(ids)))
    }


def get_cart(db: Session, user_id: int) -> dict:
    """购物车列表 + 合计（对齐 api-design §7.1）。

    - 下架/停售项仍保留在购物车（onSale=false），前端置灰
    - totalPrice/totalQuantity 仅统计可售勾选项：onSale 且可用库存 > 0 且勾选
    """
    repo = CartRepository(db)
    items = repo.list_by_user(user_id)
    if not items:
        return CartStateOut().model_dump(by_alias=True)

    products = _load_products(db, {i.product_id for i in items})
    skus = _load_skus(db, {i.sku_id for i in items})

    out_list: list[CartItemOut] = []
    total_price = Decimal("0.00")
    total_quantity = 0

    for item in items:
        product = products.get(item.product_id)
        sku = skus.get(item.sku_id)
        if product is None or sku is None:
            # 商品/SKU 已物理删除：跳过展示但保留数据
            continue

        on_sale = product.status == 1 and sku.status == 1
        available = _available_stock(sku)
        price = sku.price if sku.price is not None else Decimal("0.00")

        out_list.append(
            CartItemOut(
                id=item.id,
                product_id=item.product_id,
                sku_id=item.sku_id,
                name=product.name,
                sku_text=sku.sku_text,
                price=float(price),
                quantity=item.quantity,
                image=sku.image or product.main_image,
                selected=item.selected,
                stock=available,
                on_sale=on_sale,
            )
        )

        if on_sale and available > 0 and item.selected:
            total_price += price * item.quantity
            total_quantity += item.quantity

    state = CartStateOut(
        items=out_list,
        total_price=float(total_price),
        total_quantity=total_quantity,
    )
    return state.model_dump(by_alias=True)


def add_item(
    db: Session, user_id: int, sku_id: int, quantity: int = 1, selected: bool = False
) -> dict:
    """加入购物车（对齐 api-design §7.2 / test-cases B3-3/B3-4/B3-5）。

    同一 SKU 已存在则数量累加；新增项默认不勾选（selected=False）。
    """
    product, sku = _get_saleable_sku(db, sku_id)
    available = _available_stock(sku)

    repo = CartRepository(db)
    existing = repo.get_by_user_sku(user_id, sku_id)
    if existing:
        new_quantity = _validate_quantity(existing.quantity + quantity, available)
        existing.quantity = new_quantity
        repo.save(existing)
    else:
        _validate_quantity(quantity, available)
        repo.save(
            Cart(
                user_id=user_id,
                product_id=product.id,
                sku_id=sku_id,
                quantity=quantity,
                selected=selected,
            )
        )
    db.commit()
    return get_cart(db, user_id)


def update_item(
    db: Session,
    user_id: int,
    item_id: int,
    quantity: int | None = None,
    selected: bool | None = None,
    sku_id: int | None = None,
) -> dict:
    """修改购物车项（对齐 api-design §7.3 / test-cases B3-6/B3-6a）。

    - quantity=0 → 删除该项；quantity 超限 → 1201 / 1104
    - skuId 换规格：仅允许同商品其他 SKU（跨商品 → 400）；目标 SKU 已在购物车则合并数量
    """
    repo = CartRepository(db)
    item = repo.get_owned(user_id, item_id)
    if item is None:
        raise BizException(404, "购物车项不存在")

    # 换规格：优先处理，可能直接合并删除当前项
    if sku_id is not None and sku_id != item.sku_id:
        target, target_sku = _get_saleable_sku(db, sku_id)
        if target.id != item.product_id:
            raise BizException(400, "不能跨商品更换规格")

        target_available = _available_stock(target_sku)
        merged = repo.get_by_user_sku(user_id, sku_id)
        if merged is not None and merged.id != item.id:
            # 目标 SKU 已在购物车：数量累加（显式 quantity 优先，否则并入原项数量），移除原项
            add_qty = quantity if quantity is not None else item.quantity
            merged.quantity = _validate_quantity(merged.quantity + add_qty, target_available)
            repo.save(merged)
            repo.delete(item)
            db.commit()
            return get_cart(db, user_id)
        # 普通换规格：更新 SKU 并校验新 SKU 库存
        if quantity is not None:
            _validate_quantity(quantity, target_available)
        item.sku_id = sku_id
        repo.save(item)

    # 改数量（quantity=0 视为删除）
    if quantity is not None:
        if quantity == 0:
            repo.delete(item)
            db.commit()
            return get_cart(db, user_id)
        cur_sku = db.get(ProductSku, item.sku_id)
        available = _available_stock(cur_sku) if cur_sku else 0
        _validate_quantity(quantity, available)
        item.quantity = quantity
        repo.save(item)

    # 改勾选
    if selected is not None:
        item.selected = selected
        repo.save(item)

    db.commit()
    return get_cart(db, user_id)


def delete_items(db: Session, user_id: int, ids: list[int]) -> dict:
    """批量删除（对齐 api-design §7.5 / test-cases B3-7）。"""
    if not ids:
        raise BizException(400, "ids 不能为空")
    repo = CartRepository(db)
    repo.delete_owned(user_id, ids)
    db.commit()
    return get_cart(db, user_id)


def select_all(db: Session, user_id: int, selected: bool) -> dict:
    """全选/取消全选（对齐 api-design §7.6 / test-cases B3-8/B3-9）。

    - 全选：仅勾选可售项（onSale 且可用库存 > 0），失效项置为不勾选
    - 取消全选：清空全部勾选（含失效项），保证直购链路不受历史勾选干扰
    """
    repo = CartRepository(db)
    if not selected:
        repo.set_all_selected(user_id, False)
        db.commit()
        return get_cart(db, user_id)

    items = repo.list_by_user(user_id)
    saleable_ids: list[int] = []
    for item in items:
        sku = db.get(ProductSku, item.sku_id)
        if sku is None or sku.deleted or sku.status != 1:
            continue
        product = db.get(Product, item.product_id)
        if product is None or product.deleted or product.status != 1:
            continue
        if _available_stock(sku) > 0:
            saleable_ids.append(item.id)

    # 可售项全部勾选，其余失效项取消勾选
    repo.set_select_where(user_id, saleable_ids, True)
    if saleable_ids:
        repo.set_select_where(
            user_id, [i.id for i in items if i.id not in saleable_ids], False
        )
    db.commit()
    return get_cart(db, user_id)
