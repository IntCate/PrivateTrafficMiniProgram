"""认证模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from app.common.schemas import CamelModel, CamelRequest


class LoginRequest(CamelRequest):
    """微信登录入参。"""

    code: str
    nickname: str | None = None
    avatar: str | None = None


class MemberOut(CamelModel):
    """会员对外信息（不含 openid/unionid/session_key 等敏感字段）。"""

    id: int
    nickname: str | None = None
    avatar: str | None = None
    member_level: str | None = None
    points: int = 0
    phone: str | None = None


class LoginResponse(CamelModel):
    """登录出参。"""

    token: str
    expires_in: int
    member: MemberOut
