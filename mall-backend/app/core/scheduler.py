"""APScheduler 调度器初始化与统一注册入口。"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.modules.order.tasks import close_timeout_orders_job

logger = logging.getLogger("app.core.scheduler")

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def init_scheduler() -> None:
    """启动调度器并注册业务任务。"""
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler started")
    register_interval_job(
        close_timeout_orders_job,
        seconds=60,
        job_id="order_close_timeout",
    )


def register_interval_job(func: object, seconds: int, job_id: str) -> None:
    """注册一个按秒周期执行的任务。"""
    scheduler.add_job(
        func,
        trigger=IntervalTrigger(seconds=seconds),
        id=job_id,
        replace_existing=True,
    )
