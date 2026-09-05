"""后台管理模块 Pydantic 模型。对齐 docs/api-design.md §13。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """后台登录请求。"""

    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class LoginOut(BaseModel):
    """后台登录响应。"""

    token: str
    admin: AdminUserOut


class AdminUserOut(BaseModel):
    """管理员信息（永不返回密码）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    role: str
    status: int


class AdminUserItemOut(BaseModel):
    """管理员列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    role: str
    status: int
    last_login_at: datetime | None = None
    created_at: datetime


class CreateAdminRequest(BaseModel):
    """创建管理员。"""

    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=32)
    role: str = Field(default="operator", pattern="^(admin|operator|finance)$")


class UpdateAdminStatusRequest(BaseModel):
    """更新管理员状态。"""

    status: int = Field(ge=0, le=1)


class ProductAdminItemOut(BaseModel):
    """后台商品列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_no: str
    name: str
    category_id: int
    price: Decimal
    stock: int
    sales: int
    status: int
    created_at: datetime


class ProductAdminDetailOut(BaseModel):
    """后台商品详情。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_no: str
    category_id: int
    brand: str | None = None
    name: str
    sub_title: str | None = None
    price: Decimal
    original_price: Decimal | None = None
    main_image: str
    images: list[str] = Field(default_factory=list)
    detail_html: str | None = None
    spec: dict | None = None
    sales: int
    stock: int
    tags: list[str] = Field(default_factory=list)
    shipping_from: str | None = None
    is_free_shipping: bool
    status: int
    views: int


class CreateProductRequest(BaseModel):
    """创建商品。"""

    product_no: str = Field(min_length=1, max_length=32)
    category_id: int
    brand: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    sub_title: str | None = Field(default=None, max_length=255)
    price: Decimal = Field(ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    main_image: str = Field(min_length=1, max_length=512)
    images: list[str] = Field(default_factory=list)
    detail_html: str | None = None
    spec: dict | None = None
    stock: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)
    shipping_from: str | None = Field(default=None, max_length=32)
    is_free_shipping: bool = True
    status: int = Field(default=1, ge=0, le=1)


class UpdateProductRequest(BaseModel):
    """更新商品。"""

    category_id: int | None = None
    brand: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    sub_title: str | None = Field(default=None, max_length=255)
    price: Decimal | None = Field(default=None, ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    main_image: str | None = Field(default=None, max_length=512)
    images: list[str] | None = None
    detail_html: str | None = None
    spec: dict | None = None
    stock: int | None = Field(default=None, ge=0)
    tags: list[str] | None = None
    shipping_from: str | None = Field(default=None, max_length=32)
    is_free_shipping: bool | None = None
    status: int | None = Field(default=None, ge=0, le=1)


class UpdateProductStatusRequest(BaseModel):
    """上下架。"""

    status: int = Field(ge=0, le=1)


class ProductSkuAdminItemOut(BaseModel):
    """后台商品 SKU 项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    sku_code: str
    attrs: list[dict] = Field(default_factory=list)
    sku_text: str
    price: Decimal
    stock: int
    lock_stock: int
    image: str | None = None
    status: int


class CreateProductSkuRequest(BaseModel):
    """创建 SKU。"""

    sku_code: str = Field(min_length=1, max_length=64)
    attrs: list[dict] = Field(default_factory=list)
    sku_text: str = Field(min_length=1, max_length=128)
    price: Decimal = Field(ge=0, default=Decimal("0.00"))
    stock: int = Field(default=0, ge=0)
    image: str | None = Field(default=None, max_length=512)
    status: int = Field(default=1, ge=0, le=1)


class UpdateProductSkuRequest(BaseModel):
    """更新 SKU。"""

    sku_code: str | None = Field(default=None, min_length=1, max_length=64)
    attrs: list[dict] | None = None
    sku_text: str | None = Field(default=None, min_length=1, max_length=128)
    price: Decimal | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    image: str | None = Field(default=None, max_length=512)
    status: int | None = Field(default=None, ge=0, le=1)


class CategoryAdminItemOut(BaseModel):
    """后台分类项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int
    name: str
    icon: str | None = None
    sort: int
    status: int


class CreateCategoryRequest(BaseModel):
    """创建分类。"""

    parent_id: int = Field(default=0, ge=0)
    name: str = Field(min_length=1, max_length=64)
    icon: str | None = Field(default=None, max_length=512)
    sort: int = Field(default=0)
    status: int = Field(default=1, ge=0, le=1)


class UpdateCategoryRequest(BaseModel):
    """更新分类。"""

    parent_id: int | None = Field(default=None, ge=0)
    name: str | None = Field(default=None, min_length=1, max_length=64)
    icon: str | None = Field(default=None, max_length=512)
    sort: int | None = None
    status: int | None = Field(default=None, ge=0, le=1)


class OrderAdminItemOut(BaseModel):
    """后台订单列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: int
    status: str
    pay_amount: Decimal
    receiver_name: str
    receiver_phone: str
    created_at: datetime


class OrderAdminDetailOut(BaseModel):
    """后台订单详情。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: int
    status: str
    total_amount: Decimal
    freight: Decimal
    pay_amount: Decimal
    coupon_amount: Decimal
    points_used: int
    receiver_name: str
    receiver_phone: str
    receiver_region: str
    receiver_detail: str
    pay_type: str | None = None
    transaction_id: str | None = None
    remark: str | None = None
    cancel_reason: str | None = None
    refund_reason: str | None = None
    created_at: datetime


class ShipOrderRequest(BaseModel):
    """发货请求。"""

    tracking_no: str | None = Field(default=None, max_length=64)


class MemberAdminItemOut(BaseModel):
    """后台会员列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str | None = None
    phone: str | None = None
    member_level: str
    points: int
    status: int
    created_at: datetime


class UpdateMemberStatusRequest(BaseModel):
    """更新会员状态。"""

    status: int = Field(ge=0, le=1)


class BannerAdminItemOut(BaseModel):
    """后台运营位项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    position: str
    title: str
    sub_title: str | None = None
    image: str
    link_type: str
    link_value: str | None = None
    sort: int
    status: int


class CreateBannerRequest(BaseModel):
    """创建运营位。"""

    position: str = Field(pattern="^(hero|theme)$")
    title: str = Field(min_length=1, max_length=64)
    sub_title: str | None = Field(default=None, max_length=64)
    image: str = Field(min_length=1, max_length=512)
    link_type: str = Field(default="none", pattern="^(none|product|category|page)$")
    link_value: str | None = Field(default=None, max_length=255)
    sort: int = Field(default=0)
    status: int = Field(default=1, ge=0, le=1)


class UpdateBannerRequest(BaseModel):
    """更新运营位。"""

    position: str | None = Field(default=None, pattern="^(hero|theme)$")
    title: str | None = Field(default=None, min_length=1, max_length=64)
    sub_title: str | None = Field(default=None, max_length=64)
    image: str | None = Field(default=None, max_length=512)
    link_type: str | None = Field(default=None, pattern="^(none|product|category|page)$")
    link_value: str | None = Field(default=None, max_length=255)
    sort: int | None = None
    status: int | None = Field(default=None, ge=0, le=1)


class CouponAdminItemOut(BaseModel):
    """后台优惠券项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    amount: Decimal | None = None
    discount: Decimal | None = None
    min_amount: Decimal
    total_count: int
    received_count: int
    valid_start: datetime | None = None
    valid_end: datetime | None = None
    status: int


class CreateCouponRequest(BaseModel):
    """创建优惠券。"""

    name: str = Field(min_length=1, max_length=64)
    type: str = Field(pattern="^(cash|discount|shipping)$")
    amount: Decimal | None = Field(default=None, ge=0)
    discount: Decimal | None = Field(default=None, ge=0, le=1)
    min_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_count: int = Field(default=0, ge=0)
    valid_start: datetime | None = None
    valid_end: datetime | None = None
    status: int = Field(default=1, ge=0, le=1)


class UpdateCouponRequest(BaseModel):
    """更新优惠券。"""

    name: str | None = Field(default=None, min_length=1, max_length=64)
    type: str | None = Field(default=None, pattern="^(cash|discount|shipping)$")
    amount: Decimal | None = Field(default=None, ge=0)
    discount: Decimal | None = Field(default=None, ge=0, le=1)
    min_amount: Decimal | None = Field(default=None, ge=0)
    total_count: int | None = Field(default=None, ge=0)
    valid_start: datetime | None = None
    valid_end: datetime | None = None
    status: int | None = Field(default=None, ge=0, le=1)


class GrantCouponRequest(BaseModel):
    """发放优惠券。"""

    user_id: int
    count: int = Field(default=1, ge=1, le=100)


class AfterSaleAdminItemOut(BaseModel):
    """后台售后单项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    user_id: int
    type: str
    reason: str
    amount: Decimal
    status: str
    audit_remark: str | None = None
    created_at: datetime


class AuditAfterSaleRequest(BaseModel):
    """售后审核。"""

    approve: bool
    remark: str | None = Field(default=None, max_length=255)


class DashboardSummaryOut(BaseModel):
    """数据概览。"""

    total_sales: Decimal
    order_count: int
    member_count: int
    product_count: int
    pending_order_count: int


class ConfigItemOut(BaseModel):
    """系统配置项。"""

    model_config = ConfigDict(from_attributes=True)

    config_key: str
    config_value: str
    remark: str | None = None


class UpdateConfigRequest(BaseModel):
    """更新系统配置。"""

    config_value: str = Field(min_length=0, max_length=4096)
    remark: str | None = Field(default=None, max_length=255)
