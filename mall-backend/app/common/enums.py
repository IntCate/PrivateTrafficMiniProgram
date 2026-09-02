"""通用枚举。"""
from __future__ import annotations

from enum import IntEnum


class OrderStatus(IntEnum):
    """订单状态机。"""

    PENDING = 0  # 待支付
    PAID = 1  # 待发货
    SHIPPED = 2  # 待收货
    COMPLETED = 3  # 已完成
    CANCELLED = 4  # 已取消
    CLOSED = 5  # 已关闭（超时未支付）


class PayMode(IntEnum):
    """支付方式。"""

    MOCK = 0
    WECHAT = 1
