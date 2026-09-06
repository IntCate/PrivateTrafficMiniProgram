"""后台管理模块路由。对齐 docs/api-design.md §13 与 auth.md §2.2 权限矩阵。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.deps import require_roles
from app.common.upload import save_bytes
from app.core.database import get_db
from app.core.response import ok
from app.modules.admin import service
from app.modules.admin.schemas import (
    AuditAfterSaleRequest,
    CreateAdminRequest,
    CreateBannerRequest,
    CreateCategoryRequest,
    CreateCouponRequest,
    CreateProductRequest,
    CreateProductSkuRequest,
    GrantCouponRequest,
    LoginRequest,
    ShipOrderRequest,
    UpdateAdminStatusRequest,
    UpdateBannerRequest,
    UpdateCategoryRequest,
    UpdateConfigRequest,
    UpdateCouponRequest,
    UpdateMemberStatusRequest,
    UpdateProductRequest,
    UpdateProductSkuRequest,
    UpdateProductStatusRequest,
)

router = APIRouter(tags=["admin"])

# 角色常量（对齐 auth.md §2.2）
ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_FINANCE = "finance"


def _admin_id(admin: dict[str, Any]) -> int:
    return int(admin["sub"])


@router.post("/login")
def do_login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """后台登录（公开）。"""
    return ok(service.login(db, body.username, body.password).model_dump())


# ---- 管理员管理（仅 admin）----


@router.get("/admins")
def do_list_admins(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.list_admins(db, page, page_size))


@router.post("/admins")
def do_create_admin(
    body: CreateAdminRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.create_admin(db, body).model_dump())


@router.put("/admins/{admin_id}/status")
def do_update_admin_status(
    admin_id: int,
    body: UpdateAdminStatusRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_admin_status(db, admin_id, body, _admin_id(admin)).model_dump())


# ---- 商品（admin/operator）----


@router.get("/products")
def do_list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    keyword: str | None = Query(default=None, max_length=50),
    category_id: int | None = Query(default=None),
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.list_products(db, page, page_size, keyword, category_id))


@router.get("/products/{product_id}")
def do_get_product(
    product_id: int,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.get_product(db, product_id).model_dump())


@router.post("/products")
def do_create_product(
    body: CreateProductRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.create_product(db, body).model_dump())


@router.put("/products/{product_id}")
def do_update_product(
    product_id: int,
    body: UpdateProductRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_product(db, product_id, body).model_dump())


@router.put("/products/{product_id}/status")
def do_update_product_status(
    product_id: int,
    body: UpdateProductStatusRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_product_status(db, product_id, body).model_dump())


@router.delete("/products/{product_id}")
def do_delete_product(
    product_id: int,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    service.delete_product(db, product_id)
    return ok({"deleted": True})


# ---- 商品 SKU（admin/operator）----


@router.get("/products/{product_id}/skus")
def do_list_product_skus(
    product_id: int,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.list_product_skus(db, product_id))


@router.post("/products/{product_id}/skus")
def do_create_product_sku(
    product_id: int,
    body: CreateProductSkuRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.create_product_sku(db, product_id, body))


@router.put("/products/{product_id}/skus/{sku_id}")
def do_update_product_sku(
    product_id: int,
    sku_id: int,
    body: UpdateProductSkuRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_product_sku(db, product_id, sku_id, body))


@router.delete("/products/{product_id}/skus/{sku_id}")
def do_delete_product_sku(
    product_id: int,
    sku_id: int,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    service.delete_product_sku(db, product_id, sku_id)
    return ok({"deleted": True})


# ---- 分类（admin/operator）----


@router.get("/categories")
def do_list_categories(
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok({"list": service.list_categories(db)})


@router.post("/categories")
def do_create_category(
    body: CreateCategoryRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.create_category(db, body))


@router.put("/categories/{category_id}")
def do_update_category(
    category_id: int,
    body: UpdateCategoryRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_category(db, category_id, body))


@router.delete("/categories/{category_id}")
def do_delete_category(
    category_id: int,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    service.delete_category(db, category_id)
    return ok({"deleted": True})


# ---- 订单（admin/operator/finance 查询，admin/operator 发货）----


@router.get("/orders")
def do_list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    status: str | None = Query(default=None),
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR, ROLE_FINANCE)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.list_orders(db, page, page_size, status))


@router.get("/orders/{order_id}")
def do_get_order(
    order_id: int,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR, ROLE_FINANCE)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.get_order(db, order_id).model_dump())


@router.put("/orders/{order_id}/ship")
def do_ship_order(
    order_id: int,
    body: ShipOrderRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.ship_order(db, order_id, body).model_dump())


# ---- 会员（admin 禁用，admin/operator/finance 查询）----


@router.get("/members")
def do_list_members(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    keyword: str | None = Query(default=None, max_length=50),
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR, ROLE_FINANCE)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.list_members(db, page, page_size, keyword))


@router.put("/members/{member_id}/status")
def do_update_member_status(
    member_id: int,
    body: UpdateMemberStatusRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_member_status(db, member_id, body))


# ---- 运营位（admin/operator）----


class UploadOut(BaseModel):
    url: str


# 允许的图片类型与体积上限（5MB）
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_SIZE = 5 * 1024 * 1024


@router.post("/upload")
def do_upload_image(
    file: UploadFile = File(...),
    category: str = Form("banner"),
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
) -> dict:
    """运营位图片上传 🔒（admin/operator）。返回可访问的相对 URL。"""
    if category not in {"banner", "product", "category"}:
        raise HTTPException(status_code=400, detail="不支持的图片用途")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 jpg/jpeg/png/gif/webp 图片")
    content = file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")
    relative = save_bytes(content, suffix, category)
    return ok(UploadOut(url=f"/uploads/{relative}").model_dump())


@router.get("/banners")
def do_list_banners(
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok({"list": service.list_banners(db)})


@router.post("/banners")
def do_create_banner(
    body: CreateBannerRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.create_banner(db, body))


@router.put("/banners/{banner_id}")
def do_update_banner(
    banner_id: int,
    body: UpdateBannerRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_banner(db, banner_id, body))


@router.delete("/banners/{banner_id}")
def do_delete_banner(
    banner_id: int,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    service.delete_banner(db, banner_id)
    return ok({"deleted": True})


# ---- 优惠券（admin/operator）----


@router.get("/coupons")
def do_list_coupons(
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok({"list": service.list_coupons(db)})


@router.post("/coupons")
def do_create_coupon(
    body: CreateCouponRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.create_coupon(db, body))


@router.put("/coupons/{coupon_id}")
def do_update_coupon(
    coupon_id: int,
    body: UpdateCouponRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_coupon(db, coupon_id, body))


@router.post("/coupons/{coupon_id}/grant")
def do_grant_coupon(
    coupon_id: int,
    body: GrantCouponRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.grant_coupon(db, coupon_id, body))


# ---- 售后（admin/operator）----


@router.get("/after-sales")
def do_list_after_sales(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    status: str | None = Query(default=None),
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.list_after_sales(db, page, page_size, status))


@router.put("/after-sales/{after_sale_id}/audit")
def do_audit_after_sale(
    after_sale_id: int,
    body: AuditAfterSaleRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.audit_after_sale(db, after_sale_id, body.approve, body.remark))


# ---- 数据概览（admin/operator/finance）----


@router.get("/dashboard/summary")
def do_dashboard_summary(
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR, ROLE_FINANCE)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.dashboard_summary(db).model_dump())


@router.get("/dashboard/trend")
def do_dashboard_trend(
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_OPERATOR, ROLE_FINANCE)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.dashboard_trend(db).model_dump())


# ---- 系统配置（仅 admin）----


@router.get("/configs")
def do_list_configs(
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    return ok({"list": service.list_configs(db)})


@router.put("/configs/{key}")
def do_update_config(
    key: str,
    body: UpdateConfigRequest,
    admin: dict[str, Any] = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.update_config(db, key, body))
