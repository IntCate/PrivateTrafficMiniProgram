"""WebSocket 端点：后台与小程序按主题订阅实时推送。

- `/admin/ws`：后台，首条消息 `{type:'auth', token}`，JWT 校验后绑定 `admin` 主题；
- `/ws/member`：小程序，首条消息 `{type:'auth', token}`，查 member_session 解析
  user_id 后绑定 `order:{user_id}` 主题。
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core import ws as ws_manager
from app.core.database import SessionLocal
from app.core.security import decode_admin_jwt
from app.modules.auth.models import MemberSession

router = APIRouter()


def _parse_auth_message(raw: str) -> dict[str, Any] | None:
    """解析首条鉴权消息，返回 dict 或 None（非法）。"""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("type") != "auth":
        return None
    token = data.get("token")
    if not token or not isinstance(token, str):
        return None
    return data


def _resolve_member_user_id(token: str) -> int | None:
    """通过会员 token 查 member_session，返回 user_id（无效返回 None）。"""
    db = SessionLocal()
    try:
        session = (
            db.query(MemberSession)
            .filter(
                MemberSession.token == token,
                MemberSession.deleted == False,  # noqa: E712
            )
            .first()
        )
        if not session or session.expires_at < datetime.now():
            return None
        return session.user_id
    finally:
        db.close()


@router.websocket("/admin/ws")
async def admin_ws(ws: WebSocket) -> None:
    """后台 WebSocket：JWT 鉴权后绑定 admin 主题。"""
    await ws.accept()
    raw = await ws.receive_text()
    msg = _parse_auth_message(raw)
    if msg is None:
        await ws.close(code=4401)
        return
    try:
        decode_admin_jwt(msg["token"])
    except jwt.PyJWTError:
        await ws.close(code=4401)
        return
    await ws_manager.connect(ws, "admin")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws, "admin")


@router.websocket("/ws/member")
async def member_ws(ws: WebSocket) -> None:
    """小程序 WebSocket：会员 token 鉴权后绑定 order:{user_id} 与 public 主题。"""
    await ws.accept()
    raw = await ws.receive_text()
    msg = _parse_auth_message(raw)
    if msg is None:
        await ws.close(code=4401)
        return
    user_id = _resolve_member_user_id(msg["token"])
    if user_id is None:
        await ws.close(code=4401)
        return
    topics = [f"order:{user_id}", "public"]
    for topic in topics:
        await ws_manager.connect(ws, topic)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        for topic in topics:
            ws_manager.disconnect(ws, topic)
