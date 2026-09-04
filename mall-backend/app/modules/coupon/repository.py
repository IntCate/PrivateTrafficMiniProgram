"""优惠券模块数据访问。"""
from __future__ import annotations

from sqlalchemy import func, select

from app.common.repository import BaseRepository
from app.modules.coupon.models import Coupon, UserCoupon


class CouponRepository(BaseRepository[Coupon]):
    model = Coupon


class UserCouponRepository(BaseRepository[UserCoupon]):
    model = UserCoupon

    def get_by_user_coupon(self, user_id: int, coupon_id: int) -> UserCoupon | None:
        """按 user + coupon 查询领取记录（幂等去重）。"""
        stmt = select(UserCoupon).where(
            UserCoupon.user_id == user_id, UserCoupon.coupon_id == coupon_id
        )
        return self.db.scalar(stmt)

    def list_by_user(
        self, user_id: int, status: str | None, page: int, page_size: int
    ) -> tuple[list[UserCoupon], int]:
        """按用户分页查询用户券（新领取在前）。"""
        cond = [UserCoupon.user_id == user_id]
        if status:
            cond.append(UserCoupon.status == status)
        count_stmt = select(func.count(UserCoupon.id)).where(*cond)
        total = self.db.scalar(count_stmt) or 0
        rows = list(
            self.db.scalars(
                select(UserCoupon)
                .where(*cond)
                .order_by(UserCoupon.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return rows, total

    def count_unused(self, user_id: int) -> int:
        """统计未使用券数量（含未过期，供会员中心角标）。"""
        stmt = select(func.count(UserCoupon.id)).where(
            UserCoupon.user_id == user_id, UserCoupon.status == "unused"
        )
        return self.db.scalar(stmt) or 0
