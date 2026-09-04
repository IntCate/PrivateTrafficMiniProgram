"""积分模块单元测试：积分明细列表。

对齐 docs/test-cases.md B8（积分）。使用内存 Fake 仓储/桩验证 service 业务分支。
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest

from app.modules.points import service


def _log(
    id: int,
    *,
    user_id: int = 1,
    change: int = 100,
    balance: int = 100,
    type: str = "earn",
    biz_type: str = "order",
    remark: str = "订单完成获得积分",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        user_id=user_id,
        change=change,
        balance=balance,
        type=type,
        biz_type=biz_type,
        remark=remark,
        created_at=datetime(2026, 9, 1, 10, 0, 0),
    )


class FakeDb:
    """内存 Session：支持 scalar 查询（供 PointsLogRepository）。"""

    def __init__(self, logs: dict[int, SimpleNamespace]) -> None:
        self._logs = logs

    def scalar(self, stmt: object) -> object | None:
        return len(self._logs)

    def scalars(self, stmt: object) -> list[SimpleNamespace]:
        return list(self._logs.values())


class FakePointsLogRepo:
    """内存积分明细仓储。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db

    def list_by_user(
        self, user_id: int, page: int, page_size: int
    ) -> tuple[list[SimpleNamespace], int]:
        rows = [log for log in self.db._logs.values() if log.user_id == user_id]
        rows.sort(key=lambda log: log.id, reverse=True)
        total = len(rows)
        start = (page - 1) * page_size
        return rows[start : start + page_size], total


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> FakeDb:
    db = FakeDb(
        {
            1: _log(1),
            2: _log(2, change=-50, balance=50, type="consume", remark="订单积分抵扣"),
        }
    )
    monkeypatch.setattr(service, "PointsLogRepository", lambda d: FakePointsLogRepo(d))
    return db


# ---- B8-3 积分明细列表 ----

def test_list_points_logs_ok(env: FakeDb) -> None:
    data = service.list_points_logs(env, 1, 1, 10)
    assert data.total == 2
    assert data.items[0].change == -50
    assert data.items[0].type == "consume"
    assert data.items[1].change == 100
    assert data.items[1].type == "earn"


def test_list_points_logs_pagination(env: FakeDb) -> None:
    data = service.list_points_logs(env, 1, 1, 1)
    assert data.total == 2
    assert len(data.items) == 1
    assert data.has_more is True
