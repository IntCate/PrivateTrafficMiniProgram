"""WebSocket 连接管理器：按主题维护连接，支持定向/广播推送。

- `notify`：供同步 service 层调用（运行在 FastAPI 事件循环内），异步提交不阻塞事务；
- `notify_threadsafe`：供定时任务（独立线程）调用，跨线程提交到主事件循环。
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("app.core.ws")

_connections: dict[str, set[WebSocket]] = {}

# 主事件循环引用：应用启动时由 lifespan 保存，供跨线程推送使用
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    """保存主事件循环引用（应用启动/关闭时调用）。"""
    global _main_loop
    _main_loop = loop


async def connect(ws: WebSocket, topic: str) -> None:
    _connections.setdefault(topic, set()).add(ws)
    logger.info("ws connected topic=%s total=%d", topic, len(_connections[topic]))


def disconnect(ws: WebSocket, topic: str) -> None:
    conns = _connections.get(topic)
    if conns:
        conns.discard(ws)
        if not conns:
            _connections.pop(topic, None)


async def _send(ws: WebSocket, event: str, payload: dict[str, Any] | None) -> None:
    await ws.send_json({"event": event, "data": payload or {}})


async def send_to_topic(topic: str, event: str, payload: dict[str, Any] | None = None) -> None:
    """向某主题的所有连接推送一条事件。"""
    conns = _connections.get(topic)
    if not conns:
        return
    dead: list[WebSocket] = []
    for ws in list(conns):
        try:
            await _send(ws, event, payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        disconnect(ws, topic)


def notify(topic: str, event: str, payload: dict[str, Any] | None = None) -> None:
    """同步入口：供同步 service 层调用，异步提交到事件循环，不阻塞业务事务。

    优先使用当前运行中的事件循环；若在同步 def（线程池）中调用则回退到主事件循环。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = _main_loop
    if loop is None or loop.is_closed():
        return
    if loop.is_running():
        asyncio.run_coroutine_threadsafe(send_to_topic(topic, event, payload), loop)
    else:
        loop.create_task(send_to_topic(topic, event, payload))


def notify_threadsafe(topic: str, event: str, payload: dict[str, Any] | None = None) -> None:
    """线程安全入口：供定时任务（独立线程）调用，跨线程提交到主事件循环。"""
    loop = _main_loop
    if loop is None or loop.is_closed():
        return
    asyncio.run_coroutine_threadsafe(send_to_topic(topic, event, payload), loop)
