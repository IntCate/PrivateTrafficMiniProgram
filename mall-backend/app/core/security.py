"""安全：密码哈希、token 生成/校验、鉴权守卫。"""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def generate_member_token() -> str:
    """C 端会员不透明 token（约 43 字符，不可推断用户）。"""
    return secrets.token_urlsafe(32)


def create_admin_jwt(admin_id: int, role: str) -> str:
    """签发后台 JWT。"""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(admin_id),
        "role": role,
        "jti": secrets.token_hex(16),
        "iat": now,
        "exp": now + timedelta(hours=settings.admin_jwt_ttl_hours),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_admin_jwt(token: str) -> dict[str, Any]:
    """解码并校验后台 JWT，失败抛异常。"""
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
