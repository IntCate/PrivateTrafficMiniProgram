"""JSON 日志、request_id 中间件、脱敏。"""
from __future__ import annotations

import json
import logging
import logging.handlers
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JsonFormatter(logging.Formatter):
    """单行 JSON 日志格式化器。"""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id_var.get(),
            "msg": record.getMessage(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            entry.update(extra)
        return json.dumps(entry, ensure_ascii=False)


def setup_logging() -> None:
    """初始化根日志器：控制台 + 按日轮转文件。"""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    formatter = JsonFormatter()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / "app.log", when="midnight", backupCount=30, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """为每个请求生成 request_id，写入 contextvar 并回传响应头。"""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = uuid.uuid4().hex
        request_id_var.set(request_id)
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        cost_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Request-Id"] = request_id
        logging.getLogger("app.access").info(
            "access",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "cost_ms": cost_ms,
                "ip": request.client.host if request.client else "",
            },
        )
        return response
