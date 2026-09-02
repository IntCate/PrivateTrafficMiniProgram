"""认证模块路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.modules.auth.schemas import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    """微信静默登录（骨架占位，业务逻辑待实现）。"""
    return ok()
