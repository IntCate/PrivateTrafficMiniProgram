"""订单模块定时任务：超时未支付订单自动关闭。

对齐 PRD §4.2 / api-design §16.4：超时未支付（默认 30 分钟）由定时任务关闭订单并回补 lock_stock。
"""
from __future__ import annotations

import logging

from app.core.database import SessionLocal
from app.modules.order.service import close_timeout_orders

logger = logging.getLogger("app.modules.order.tasks")


def close_timeout_orders_job() -> None:
    """扫描并关闭超时未支付订单（幂等，重复执行无害）。"""
    db = SessionLocal()
    try:
        closed = close_timeout_orders(db)
        if closed:
            logger.info("closed %d timeout orders", closed)
    except Exception:
        logger.exception("close timeout orders failed")
        db.rollback()
    finally:
        db.close()
