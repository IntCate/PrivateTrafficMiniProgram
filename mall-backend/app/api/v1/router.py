"""所有模块路由统一注册点。"""
from __future__ import annotations

from fastapi import APIRouter

from app.modules.address.api import router as address_router
from app.modules.admin.api import router as admin_router
from app.modules.after_sale.api import router as after_sale_router
from app.modules.auth.api import router as auth_router
from app.modules.cart.api import router as cart_router
from app.modules.coupon.api import router as coupon_router
from app.modules.favorite.api import router as favorite_router
from app.modules.member.api import router as member_router
from app.modules.order.api import router as order_router
from app.modules.points.api import router as points_router
from app.modules.product.api import (
    category_router,
    home_router,
    product_router,
)

api_router = APIRouter()

# C 端
api_router.include_router(auth_router, prefix="/api")
api_router.include_router(member_router, prefix="/api")
api_router.include_router(home_router, prefix="/api")
api_router.include_router(category_router, prefix="/api")
api_router.include_router(product_router, prefix="/api")
api_router.include_router(cart_router, prefix="/api")
api_router.include_router(address_router, prefix="/api")
api_router.include_router(order_router, prefix="/api")
api_router.include_router(favorite_router, prefix="/api")
api_router.include_router(after_sale_router, prefix="/api")
api_router.include_router(coupon_router, prefix="/api")
api_router.include_router(points_router, prefix="/api")

# 后台
api_router.include_router(admin_router, prefix="/admin/api")
