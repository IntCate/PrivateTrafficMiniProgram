"""FastAPI 入口：中间件、路由注册、启动事件。"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestIdMiddleware, setup_logging
from app.core.scheduler import init_scheduler

setup_logging()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router)

# 上传文件静态访问：/uploads/<relative path>
assets_dir = Path(settings.upload_dir)
assets_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=assets_dir), name="uploads")


@app.on_event("startup")
async def on_startup() -> None:
    init_scheduler()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
