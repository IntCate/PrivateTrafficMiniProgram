"""认证模块单元测试：code2session 错误映射。"""
from __future__ import annotations

import asyncio

import pytest

from app.core.exceptions import BizException
from app.modules.auth import service
from app.modules.auth.service import _exchange_openid


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


def test_exchange_openid_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake(code: str) -> dict:
        return {"openid": "mock_code", "session_key": "k"}

    monkeypatch.setattr(service, "code2session", _fake)
    result = _run(_exchange_openid("code"))
    assert result["openid"] == "mock_code"


def test_exchange_openid_wechat_errcode(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake(code: str) -> dict:
        return {"errcode": 40029, "errmsg": "invalid code"}

    monkeypatch.setattr(service, "code2session", _fake)
    with pytest.raises(BizException) as exc:
        _run(_exchange_openid("code"))
    assert exc.value.code == 1001


def test_exchange_openid_missing_openid(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake(code: str) -> dict:
        return {"session_key": "k"}

    monkeypatch.setattr(service, "code2session", _fake)
    with pytest.raises(BizException) as exc:
        _run(_exchange_openid("code"))
    assert exc.value.code == 1001


def test_exchange_openid_call_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fail(code: str) -> dict:
        raise RuntimeError("network down")

    monkeypatch.setattr(service, "code2session", _fail)
    with pytest.raises(BizException) as exc:
        _run(_exchange_openid("code"))
    assert exc.value.code == 1801
