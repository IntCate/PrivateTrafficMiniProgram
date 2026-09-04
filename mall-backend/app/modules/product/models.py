"""商品模块 ORM 模型：分类、商品、SKU、运营位。对齐 docs/database-design.md §3.2-3.4/§3.13。"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, BaseFields, SoftDeleteMixin

# 商品状态（对应 DB status）：1 上架 / 0 下架
PRODUCT_STATUS_ON = 1
PRODUCT_STATUS_OFF = 0

# 运营位 position
BANNER_POS_HERO = "hero"
BANNER_POS_THEME = "theme"


class Category(Base, BaseFields):
    """商品分类。"""

    __tablename__ = "category"

    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="父分类 ID，0 为顶级")
    name: Mapped[str] = mapped_column(String(64), comment="分类名")
    icon: Mapped[str | None] = mapped_column(String(512), comment="分类图标")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序，越小越靠前")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1 启用 / 0 停用")


class Product(Base, BaseFields, SoftDeleteMixin):
    """商品。"""

    __tablename__ = "product"

    product_no: Mapped[str] = mapped_column(String(32), unique=True, comment="商品编号")
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("category.id"), index=True, comment="所属分类"
    )
    brand: Mapped[str | None] = mapped_column(String(64), comment="品牌")
    name: Mapped[str] = mapped_column(String(128), comment="商品名称")
    sub_title: Mapped[str | None] = mapped_column(String(255), comment="副标题/卖点")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="销售价")
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="划线价/原价")
    main_image: Mapped[str] = mapped_column(String(512), comment="主图")
    images: Mapped[list[Any] | None] = mapped_column(JSON, comment="图片列表(JSON)")
    detail_html: Mapped[str | None] = mapped_column(Text, comment="详情富文本")
    spec: Mapped[dict[Any, Any] | None] = mapped_column(JSON, comment="参数规格(JSON)")
    sales: Mapped[int] = mapped_column(Integer, default=0, comment="已售数量")
    stock: Mapped[int] = mapped_column(Integer, default=0, comment="总库存")
    tags: Mapped[list[Any] | None] = mapped_column(JSON, comment="标签(JSON)")
    shipping_from: Mapped[str | None] = mapped_column(String(32), comment="发货地")
    is_free_shipping: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="1 包邮 / 0 不包邮"
    )
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1 上架 / 0 下架")
    views: Mapped[int] = mapped_column(Integer, default=0, comment="浏览量")


class ProductSku(Base, BaseFields, SoftDeleteMixin):
    """商品 SKU。"""

    __tablename__ = "product_sku"

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), index=True, comment="商品 ID"
    )
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, comment="SKU 编码")
    attrs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, comment="属性组(JSON)")
    sku_text: Mapped[str] = mapped_column(String(128), comment="展示文案")
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="SKU 售价"
    )
    stock: Mapped[int] = mapped_column(Integer, default=0, comment="库存")
    lock_stock: Mapped[int] = mapped_column(Integer, default=0, comment="锁定库存")
    image: Mapped[str | None] = mapped_column(String(512), comment="SKU 专属图")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1 可售 / 0 停售")


class Banner(Base, BaseFields):
    """运营位：hero 主横幅 / theme 主题精选。"""

    __tablename__ = "banner"

    position: Mapped[str] = mapped_column(String(20), index=True, comment="hero / theme")
    title: Mapped[str] = mapped_column(String(64), comment="标题")
    sub_title: Mapped[str | None] = mapped_column(String(64), comment="副标题/描述")
    image: Mapped[str] = mapped_column(String(512), comment="图片")
    link_type: Mapped[str] = mapped_column(
        String(20), default="none", comment="none/product/category/page"
    )
    link_value: Mapped[str | None] = mapped_column(String(255), comment="跳转目标")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1 展示 / 0 隐藏")
