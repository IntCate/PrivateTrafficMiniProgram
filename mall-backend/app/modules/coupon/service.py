"""优惠券模块业务逻辑。对齐 docs/api-design.md §11.3 与 database-design §3.10/§3.11。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.coupon.models import Coupon, UserCoupon
from app.modules.coupon.repository import UserCouponRepository
from app.modules.coupon.schemas import CouponActionOut, CouponItemOut, CouponListOut


def _fmt_dt(dt: datetime | None) -> str | None:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


def receive_coupon(db: Session, user_id: int, coupon_id: int) -> CouponActionOut:
    """领取优惠券（对齐 api-design §11.3 / error-code 1601-1603）。

    - 券不存在：1601
    - 已领取：1602（幂等返回 existed=true）
    - 已停用/未到生效期/已过期：1603
    - 发放总量已领完：1603
    """
    coupon = db.get(Coupon, coupon_id)
    if coupon is None:
        raise BizException(1601, "优惠券不存在")

    repo = UserCouponRepository(db)
    if repo.get_by_user_coupon(user_id, coupon_id) is not None:
        return CouponActionOut(user_coupon_id=0, existed=True)

    now = datetime.now()
    if coupon.status != 1:
        raise BizException(1603, "优惠券已过期或未到生效期")
    if coupon.valid_start and now < coupon.valid_start:
        raise BizException(1603, "优惠券已过期或未到生效期")
    if coupon.valid_end and now > coupon.valid_end:
        raise BizException(1603, "优惠券已过期或未到生效期")
    if coupon.total_count > 0 and coupon.received_count >= coupon.total_count:
        raise BizException(1603, "优惠券已过期或未到生效期")

    coupon.received_count += 1
    uc = UserCoupon(user_id=user_id, coupon_id=coupon_id, status="unused")
    db.add(uc)
    db.flush()
    db.commit()
    return CouponActionOut(user_coupon_id=uc.id, existed=False)


def list_coupons(
    db: Session, user_id: int, status: str | None, page: int, page_size: int
) -> CouponListOut:
    """用户优惠券列表（对齐 api-design §11.3）。"""
    repo = UserCouponRepository(db)
    rows, total = repo.list_by_user(user_id, status, page, page_size)
    items = _build_items(db, rows)
    return CouponListOut(
        items=items, total=total, page=page, page_size=page_size, has_more=page * page_size < total
    )


def _build_items(db: Session, rows: list[UserCoupon]) -> list[CouponItemOut]:
    if not rows:
        return []
    coupon_ids = {r.coupon_id for r in rows}
    coupons = {c.id: c for c in db.scalars(select(Coupon).where(Coupon.id.in_(coupon_ids)))}
    return [
        CouponItemOut(
            id=r.id,
            coupon_id=r.coupon_id,
            name=coupons[r.coupon_id].name if r.coupon_id in coupons else "",
            type=coupons[r.coupon_id].type if r.coupon_id in coupons else "",
            amount=_to_float(coupons[r.coupon_id].amount) if r.coupon_id in coupons else None,
            discount=_to_float(coupons[r.coupon_id].discount)
            if r.coupon_id in coupons
            else None,
            min_amount=float(coupons[r.coupon_id].min_amount)
            if r.coupon_id in coupons
            else 0.0,
            status=r.status,
            valid_start=_fmt_dt(coupons[r.coupon_id].valid_start)
            if r.coupon_id in coupons
            else None,
            valid_end=_fmt_dt(coupons[r.coupon_id].valid_end)
            if r.coupon_id in coupons
            else None,
        )
        for r in rows
    ]


def _to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None
