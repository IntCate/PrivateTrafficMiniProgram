"""微信对接：code2Session、getPhoneNumber（骨架占位）。"""
from __future__ import annotations

import httpx

from app.core.config import settings


async def code2session(code: str) -> dict:
    """调用微信 code2session 换取 openid/session_key。"""
    if settings.login_mock:
        # 开发期 mock：code 传任意值，生成稳定 mock openid
        return {"openid": f"mock_{code}", "session_key": "mock_session_key"}
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.wx_app_id,
        "secret": settings.wx_app_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
