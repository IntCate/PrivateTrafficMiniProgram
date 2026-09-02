"""通用依赖：get_db / get_current_member / get_current_admin / require_roles / pagination。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.security import decode_admin_jwt
from app.modules.auth.models import Member, MemberSession


def get_bearer_token(authorization: str | None = Header(default=None)) -> str | None:
    """从 Authorization 头解析 Bearer token。"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization[len("Bearer ") :].strip()


def get_current_member(
    token: str | None = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> Member:
    """C 端会员鉴权：解析 token → 查 member_session（未过期）→ 返回会员。

    对齐 docs/conventions/auth.md §1.3：会话不存在/过期/会员禁用均返回 401。
    """
    if not token:
        raise BizException(401, "未登录")

    session = (
        db.query(MemberSession)
        .filter(
            MemberSession.token == token,
            MemberSession.deleted == False,  # noqa: E712
        )
        .first()
    )
    if not session or session.expires_at < datetime.now():
        raise BizException(401, "登录过期")
    member = db.get(Member, session.user_id)
    if not member or member.deleted or member.status != 1:
        raise BizException(401, "账号已被禁用")
    return member


def get_current_admin(
    token: str | None = Depends(get_bearer_token),
) -> Any:
    """后台 JWT 鉴权：解码校验 → 返回 admin 身份。"""
    if not token:
        raise BizException(401, "未登录")
    try:
        payload = decode_admin_jwt(token)
    except jwt.PyJWTError:
        raise BizException(401, "登录过期") from None
    return payload


def require_roles(*names: str) -> Any:
    """在 get_current_admin 基础上追加角色白名单。"""

    def dependency(admin: dict[str, Any] = Depends(get_current_admin)) -> dict[str, Any]:
        if admin.get("role") not in names:
            raise BizException(403, "无操作权限")
        return admin

    return dependency


def pagination(page: int = 1, pageSize: int = 10) -> tuple[int, int]:
    """统一分页参数：page 默认 1，pageSize 默认 10 最大 50。"""
    page = max(page, 1)
    pageSize = min(max(pageSize, 1), 50)
    return page, pageSize
