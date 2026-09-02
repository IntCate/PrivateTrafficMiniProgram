"""认证模块业务逻辑：微信登录、退出登录。"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.common.utils import mask_openid
from app.core.config import settings
from app.core.exceptions import BizException
from app.core.security import generate_member_token
from app.integrations.wechat import code2session
from app.modules.auth.models import MEMBER_LEVEL_DEFAULT, Member, MemberSession
from app.modules.auth.repository import MemberRepository, MemberSessionRepository

logger = logging.getLogger("app.modules.auth.service")

# 默认昵称（对齐 PRD §4.1）
DEFAULT_NICKNAME = "快乐购物家"


async def _exchange_openid(code: str) -> dict:
    """调用微信 code2session 换取 openid/session_key。

    微信 errcode 非 0 / 响应异常统一映射为业务码 1001（登录 code 无效），
    网络/调用失败映射为 1801（见 error-code.md §3）。
    """
    try:
        resp = await code2session(code)
    except Exception as exc:  # noqa: BLE001 - 三方调用异常统一转 1801
        logger.error("code2session call failed", extra={"reason": str(exc)})
        raise BizException(1801, "微信登录服务暂不可用") from exc

    errcode = resp.get("errcode", 0)
    if errcode:
        errmsg = resp.get("errmsg", "")
        logger.warning("code2session returned error", extra={"errcode": errcode, "errmsg": errmsg})
        raise BizException(1001, "登录 code 无效")

    openid = resp.get("openid")
    if not openid:
        raise BizException(1001, "登录 code 无效")
    return resp


async def login(
    db: Session, code: str, nickname: str | None = None, avatar: str | None = None
) -> dict:
    """微信静默登录：code → openid → 自动注册/登录 → 签发 token。

    对齐 api-design §3.1 与 wechat.md §2.1。
    """
    if not code:
        raise BizException(1001, "登录 code 无效")

    result = await _exchange_openid(code)
    openid = result["openid"]

    member_repo = MemberRepository(db)
    session_repo = MemberSessionRepository(db)

    member = member_repo.get_by(openid=openid)
    is_new = member is None
    if member is None:
        member = Member(
            openid=openid,
            nickname=nickname or DEFAULT_NICKNAME,
            avatar=avatar,
            member_level=MEMBER_LEVEL_DEFAULT,
            points=0,
            status=1,
        )
        member_repo.save(member)

    if member.status != 1:
        raise BizException(1001, "账号已被禁用")

    member.last_login_at = datetime.now(UTC)
    member = member_repo.save(member)

    token = generate_member_token()
    expires_at = datetime.now(UTC) + timedelta(days=settings.token_ttl_days)
    session_repo.save(MemberSession(user_id=member.id, token=token, expires_at=expires_at))
    db.commit()

    logger.info(
        "member login",
        extra={"member_id": member.id, "openid": mask_openid(openid), "is_new": is_new},
    )

    return {
        "token": token,
        "expires_in": settings.token_ttl_days * 24 * 3600,
        "member": member,
    }


def logout(db: Session, token: str | None) -> None:
    """退出登录：删除当前会话记录。"""
    if not token:
        raise BizException(401, "未登录")
    session_repo = MemberSessionRepository(db)
    sess = session_repo.get_by(token=token)
    if sess:
        session_repo.delete(sess)
        db.commit()
