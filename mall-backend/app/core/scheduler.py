"""APScheduler 调度器初始化与统一注册入口。"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("app.core.scheduler")

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def init_scheduler() -> None:
    """启动调度器。业务任务在启动时按需注册。"""
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler started")


def register_interval_job(func: object, minutes: int, job_id: str) -> None:
    """注册一个按分钟周期执行的任务。"""
    scheduler.add_job(
        func,
        trigger=IntervalTrigger(minutes=minutes),
        id=job_id,
        replace_existing=True,
    )
