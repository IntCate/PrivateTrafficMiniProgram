"""认证模块路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps import get_bearer_token
from app.core.database import get_db
from app.core.response import ok
from app.modules.auth.schemas import LoginRequest, LoginResponse, MemberOut
from app.modules.auth.service import login, logout

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def do_login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """微信静默登录：code → openid → 自动注册/登录 → 签发 token。

    对齐 api-design §3.1。响应体不包含 openid/session_key（安全红线，见 auth.md §4）。
    """
    result = await login(db, body.code, body.nickname, body.avatar)
    data = LoginResponse(
        token=result["token"],
        expires_in=result["expires_in"],
        member=MemberOut.model_validate(result["member"]),
    )
    return ok(data.model_dump(by_alias=True))


@router.post("/logout")
def do_logout(
    token: str | None = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> dict:
    """退出登录 🔒：清除当前会话，旧 token 失效。"""
    logout(db, token)
    return ok({"loggedOut": True})
