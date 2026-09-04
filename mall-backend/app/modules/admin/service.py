"""后台管理模块业务逻辑。对齐 docs/api-design.md §13 与 auth.md §2 权限矩阵。"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.security import create_admin_jwt, hash_password, verify_password
from app.modules.admin.models import AdminUser
from app.modules.admin.repository import AdminUserRepository, SysConfigRepository
from app.modules.admin.schemas import (
    AdminUserItemOut,
    AdminUserOut,
    AfterSaleAdminItemOut,
    BannerAdminItemOut,
    CategoryAdminItemOut,
    ConfigItemOut,
    CouponAdminItemOut,
    CreateAdminRequest,
    CreateBannerRequest,
    CreateCategoryRequest,
    CreateCouponRequest,
    CreateProductRequest,
    DashboardSummaryOut,
    GrantCouponRequest,
    LoginOut,
    MemberAdminItemOut,
    OrderAdminDetailOut,
    OrderAdminItemOut,
    ProductAdminDetailOut,
    ProductAdminItemOut,
    ShipOrderRequest,
    UpdateAdminStatusRequest,
    UpdateBannerRequest,
    UpdateCategoryRequest,
    UpdateConfigRequest,
    UpdateCouponRequest,
    UpdateMemberStatusRequest,
    UpdateProductRequest,
    UpdateProductStatusRequest,
)
from app.modules.after_sale.models import (
    AFTER_SALE_APPLYING,
    AFTER_SALE_APPROVED,
    AFTER_SALE_REJECTED,
    AfterSale,
)
from app.modules.auth.models import Member
from app.modules.coupon.models import Coupon, UserCoupon
from app.modules.order.models import (
    ORDER_STATUS_PAID,
    ORDER_STATUS_PENDING,
    ORDER_STATUS_SHIPPED,
    Order,
)
from app.modules.product.models import Banner, Category, Product

logger = logging.getLogger("app.modules.admin.service")


def login(db: Session, username: str, password: str) -> LoginOut:
    """后台登录（对齐 auth.md §2.1）：账号存在、status=1、BCrypt 比对通过。"""
    admin = AdminUserRepository(db).get_by_username(username)
    if not admin or admin.status != 1 or not verify_password(password, admin.password):
        raise BizException(1701, "账号或密码错误")
    admin.last_login_at = datetime.now()
    db.commit()
    token = create_admin_jwt(admin.id, admin.role)
    return LoginOut(token=token, admin=_admin_out(admin))


def list_admins(db: Session, page: int, page_size: int) -> dict:
    """管理员列表（仅 admin 可访问）。"""
    rows, total = AdminUserRepository(db).page_admins(page, page_size)
    return {
        "list": [AdminUserItemOut.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": page * page_size < total,
    }


def create_admin(db: Session, body: CreateAdminRequest) -> AdminUserOut:
    """创建管理员（仅 admin）。"""
    repo = AdminUserRepository(db)
    if repo.get_by_username(body.username):
        raise BizException(1702, "用户名已存在")
    admin = AdminUser(
        username=body.username,
        password=hash_password(body.password),
        nickname=body.nickname,
        role=body.role,
        status=1,
    )
    repo.save(admin)
    db.commit()
    return _admin_out(admin)


def update_admin_status(
    db: Session, admin_id: int, body: UpdateAdminStatusRequest, current_admin_id: int
) -> AdminUserOut:
    """更新管理员状态（仅 admin，禁止禁用自己）。"""
    admin = db.get(AdminUser, admin_id)
    if not admin:
        raise BizException(404, "管理员不存在")
    if admin.id == current_admin_id and body.status == 0:
        raise BizException(1703, "不能禁用当前登录账号")
    admin.status = body.status
    db.commit()
    return _admin_out(admin)


def list_products(db: Session, page: int, page_size: int, keyword: str | None = None) -> dict:
    """商品列表（含关键词过滤）。"""
    stmt = select(Product).where(Product.deleted == False)  # noqa: E712
    count_stmt = select(func.count(Product.id)).where(Product.deleted == False)  # noqa: E712
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Product.name.like(like))
        count_stmt = count_stmt.where(Product.name.like(like))
    total = db.scalar(count_stmt) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Product.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return {
        "list": [ProductAdminItemOut.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": page * page_size < total,
    }


def get_product(db: Session, product_id: int) -> ProductAdminDetailOut:
    """商品详情。"""
    product = db.get(Product, product_id)
    if not product or product.deleted:
        raise BizException(404, "商品不存在")
    return ProductAdminDetailOut(
        id=product.id,
        product_no=product.product_no,
        category_id=product.category_id,
        brand=product.brand,
        name=product.name,
        sub_title=product.sub_title,
        price=product.price,
        original_price=product.original_price,
        main_image=product.main_image,
        images=product.images or [],
        detail_html=product.detail_html,
        spec=product.spec,
        sales=product.sales,
        stock=product.stock,
        tags=product.tags or [],
        shipping_from=product.shipping_from,
        is_free_shipping=bool(product.is_free_shipping),
        status=product.status,
        views=product.views,
    )


def create_product(db: Session, body: CreateProductRequest) -> ProductAdminDetailOut:
    """创建商品。"""
    if not db.get(Category, body.category_id):
        raise BizException(404, "分类不存在")
    product = Product(
        product_no=body.product_no,
        category_id=body.category_id,
        brand=body.brand,
        name=body.name,
        sub_title=body.sub_title,
        price=body.price,
        original_price=body.original_price,
        main_image=body.main_image,
        images=body.images or None,
        detail_html=body.detail_html,
        spec=body.spec,
        stock=body.stock,
        tags=body.tags or None,
        shipping_from=body.shipping_from,
        is_free_shipping=body.is_free_shipping,
        status=body.status,
    )
    db.add(product)
    db.commit()
    return get_product(db, product.id)


def update_product(
    db: Session, product_id: int, body: UpdateProductRequest
) -> ProductAdminDetailOut:
    """更新商品。"""
    product = db.get(Product, product_id)
    if not product or product.deleted:
        raise BizException(404, "商品不存在")
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(product, field, value)
    db.commit()
    return get_product(db, product_id)


def update_product_status(
    db: Session, product_id: int, body: UpdateProductStatusRequest
) -> ProductAdminDetailOut:
    """上下架。"""
    product = db.get(Product, product_id)
    if not product or product.deleted:
        raise BizException(404, "商品不存在")
    product.status = body.status
    db.commit()
    return get_product(db, product_id)


def delete_product(db: Session, product_id: int) -> None:
    """删除商品（软删）。"""
    product = db.get(Product, product_id)
    if not product or product.deleted:
        raise BizException(404, "商品不存在")
    product.deleted = True
    db.commit()


def list_categories(db: Session) -> list[dict]:
    """分类列表。"""
    rows = list(db.scalars(select(Category).order_by(Category.sort.asc(), Category.id.asc())))
    return [CategoryAdminItemOut.model_validate(r).model_dump() for r in rows]


def create_category(db: Session, body: CreateCategoryRequest) -> dict:
    """创建分类。"""
    category = Category(
        parent_id=body.parent_id,
        name=body.name,
        icon=body.icon,
        sort=body.sort,
        status=body.status,
    )
    db.add(category)
    db.commit()
    return CategoryAdminItemOut.model_validate(category).model_dump()


def update_category(
    db: Session, category_id: int, body: UpdateCategoryRequest
) -> dict:
    """更新分类。"""
    category = db.get(Category, category_id)
    if not category:
        raise BizException(404, "分类不存在")
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(category, field, value)
    db.commit()
    return CategoryAdminItemOut.model_validate(category).model_dump()


def delete_category(db: Session, category_id: int) -> None:
    """删除分类。"""
    category = db.get(Category, category_id)
    if not category:
        raise BizException(404, "分类不存在")
    db.delete(category)
    db.commit()


def list_orders(db: Session, page: int, page_size: int, status: str | None = None) -> dict:
    """订单列表。"""
    stmt = select(Order)
    count_stmt = select(func.count(Order.id))
    if status:
        stmt = stmt.where(Order.status == status)
        count_stmt = count_stmt.where(Order.status == status)
    total = db.scalar(count_stmt) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Order.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return {
        "list": [OrderAdminItemOut.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": page * page_size < total,
    }


def get_order(db: Session, order_id: int) -> OrderAdminDetailOut:
    """订单详情。"""
    order = db.get(Order, order_id)
    if not order:
        raise BizException(404, "订单不存在")
    return OrderAdminDetailOut.model_validate(order)


def ship_order(db: Session, order_id: int, body: ShipOrderRequest) -> OrderAdminDetailOut:
    """发货（仅 paid 可发货）。"""
    order = db.get(Order, order_id)
    if not order:
        raise BizException(404, "订单不存在")
    if order.status != ORDER_STATUS_PAID:
        raise BizException(1402, "订单状态不允许发货")
    order.status = ORDER_STATUS_SHIPPED
    order.ship_time = datetime.now()
    db.commit()
    return OrderAdminDetailOut.model_validate(order)


def list_members(db: Session, page: int, page_size: int, keyword: str | None = None) -> dict:
    """会员列表。"""
    stmt = select(Member).where(Member.deleted == False)  # noqa: E712
    count_stmt = select(func.count(Member.id)).where(Member.deleted == False)  # noqa: E712
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Member.nickname.like(like))
        count_stmt = count_stmt.where(Member.nickname.like(like))
    total = db.scalar(count_stmt) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Member.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return {
        "list": [MemberAdminItemOut.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": page * page_size < total,
    }


def update_member_status(
    db: Session, member_id: int, body: UpdateMemberStatusRequest
) -> dict:
    """禁用/启用会员（仅 admin）。"""
    member = db.get(Member, member_id)
    if not member or member.deleted:
        raise BizException(404, "会员不存在")
    member.status = body.status
    db.commit()
    return MemberAdminItemOut.model_validate(member).model_dump()


def list_banners(db: Session) -> list[dict]:
    """运营位列表。"""
    rows = list(db.scalars(select(Banner).order_by(Banner.position.asc(), Banner.sort.asc())))
    return [BannerAdminItemOut.model_validate(r).model_dump() for r in rows]


def create_banner(db: Session, body: CreateBannerRequest) -> dict:
    """创建运营位。"""
    banner = Banner(
        position=body.position,
        title=body.title,
        sub_title=body.sub_title,
        image=body.image,
        link_type=body.link_type,
        link_value=body.link_value,
        sort=body.sort,
        status=body.status,
    )
    db.add(banner)
    db.commit()
    return BannerAdminItemOut.model_validate(banner).model_dump()


def update_banner(db: Session, banner_id: int, body: UpdateBannerRequest) -> dict:
    """更新运营位。"""
    banner = db.get(Banner, banner_id)
    if not banner:
        raise BizException(404, "运营位不存在")
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(banner, field, value)
    db.commit()
    return BannerAdminItemOut.model_validate(banner).model_dump()


def delete_banner(db: Session, banner_id: int) -> None:
    """删除运营位。"""
    banner = db.get(Banner, banner_id)
    if not banner:
        raise BizException(404, "运营位不存在")
    db.delete(banner)
    db.commit()


def list_coupons(db: Session) -> list[dict]:
    """优惠券列表。"""
    rows = list(db.scalars(select(Coupon).order_by(Coupon.id.desc())))
    return [CouponAdminItemOut.model_validate(r).model_dump() for r in rows]


def create_coupon(db: Session, body: CreateCouponRequest) -> dict:
    """创建优惠券。"""
    coupon = Coupon(
        name=body.name,
        type=body.type,
        amount=body.amount,
        discount=body.discount,
        min_amount=body.min_amount,
        total_count=body.total_count,
        valid_start=body.valid_start,
        valid_end=body.valid_end,
        status=body.status,
    )
    db.add(coupon)
    db.commit()
    return CouponAdminItemOut.model_validate(coupon).model_dump()


def update_coupon(db: Session, coupon_id: int, body: UpdateCouponRequest) -> dict:
    """更新优惠券。"""
    coupon = db.get(Coupon, coupon_id)
    if not coupon:
        raise BizException(404, "优惠券不存在")
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(coupon, field, value)
    db.commit()
    return CouponAdminItemOut.model_validate(coupon).model_dump()


def grant_coupon(db: Session, coupon_id: int, body: GrantCouponRequest) -> dict:
    """发放优惠券给指定会员。"""
    coupon = db.get(Coupon, coupon_id)
    if not coupon:
        raise BizException(404, "优惠券不存在")
    member = db.get(Member, body.user_id)
    if not member or member.deleted:
        raise BizException(404, "会员不存在")
    for _ in range(body.count):
        db.add(
            UserCoupon(
                user_id=body.user_id,
                coupon_id=coupon_id,
                status="unused",
            )
        )
    coupon.received_count = (coupon.received_count or 0) + body.count
    db.commit()
    return {"granted": body.count}


def list_after_sales(db: Session, page: int, page_size: int, status: str | None = None) -> dict:
    """售后单列表。"""
    stmt = select(AfterSale)
    count_stmt = select(func.count(AfterSale.id))
    if status:
        stmt = stmt.where(AfterSale.status == status)
        count_stmt = count_stmt.where(AfterSale.status == status)
    total = db.scalar(count_stmt) or 0
    rows = list(
        db.scalars(
            stmt.order_by(AfterSale.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return {
        "list": [AfterSaleAdminItemOut.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": page * page_size < total,
    }


def audit_after_sale(
    db: Session, after_sale_id: int, approve: bool, remark: str | None = None
) -> dict:
    """售后审核（仅 applying 可审核）。"""
    after_sale = db.get(AfterSale, after_sale_id)
    if not after_sale:
        raise BizException(404, "售后单不存在")
    if after_sale.status != AFTER_SALE_APPLYING:
        raise BizException(1402, "售后单状态不允许审核")
    after_sale.status = AFTER_SALE_APPROVED if approve else AFTER_SALE_REJECTED
    after_sale.audit_remark = remark
    db.commit()
    return AfterSaleAdminItemOut.model_validate(after_sale).model_dump()


def dashboard_summary(db: Session) -> DashboardSummaryOut:
    """数据概览：销售额、订单量、会员数、商品数、待处理订单。"""
    total_sales = db.scalar(
        select(func.coalesce(func.sum(Order.pay_amount), 0)).where(
            Order.status.in_([ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED, "completed", "refund"])
        )
    ) or Decimal("0.00")
    order_count = db.scalar(select(func.count(Order.id))) or 0
    member_count = db.scalar(
        select(func.count(Member.id)).where(Member.deleted == False)  # noqa: E712
    ) or 0
    product_count = db.scalar(
        select(func.count(Product.id)).where(Product.deleted == False)  # noqa: E712
    ) or 0
    pending_order_count = db.scalar(
        select(func.count(Order.id)).where(Order.status == ORDER_STATUS_PENDING)
    ) or 0
    return DashboardSummaryOut(
        total_sales=total_sales,
        order_count=order_count,
        member_count=member_count,
        product_count=product_count,
        pending_order_count=pending_order_count,
    )


def list_configs(db: Session) -> list[dict]:
    """系统配置列表。"""
    rows = SysConfigRepository(db).list_all()
    return [ConfigItemOut.model_validate(r).model_dump() for r in rows]


def update_config(db: Session, key: str, body: UpdateConfigRequest) -> dict:
    """更新系统配置。"""
    config = SysConfigRepository(db).get_by_key(key)
    if not config:
        raise BizException(404, "配置不存在")
    config.config_value = body.config_value
    if body.remark is not None:
        config.remark = body.remark
    db.commit()
    return ConfigItemOut.model_validate(config).model_dump()


def _admin_out(admin: AdminUser) -> AdminUserOut:
    return AdminUserOut(
        id=admin.id,
        username=admin.username,
        nickname=admin.nickname,
        role=admin.role,
        status=admin.status,
    )
