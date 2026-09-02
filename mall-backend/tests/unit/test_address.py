"""收货地址模块单元测试：列表排序、新增、编辑、删除、设默认。

对齐 docs/test-cases.md B4。使用内存 Fake 仓储验证 service 业务分支。
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.address import service
from app.modules.address.models import ADDRESS_MAX_COUNT
from app.modules.address.schemas import AddressRequest


def _req(**overrides: object) -> AddressRequest:
    """构造合法请求体，可覆盖字段。"""
    base: dict[str, object] = {
        "name": "王小悦",
        "phone": "13812345678",
        "province": "上海市",
        "city": "上海市",
        "district": "浦东新区",
        "detail": "张江高科技园区 1 号楼 501 室",
        "is_default": False,
    }
    base.update(overrides)
    return AddressRequest(**base)


def _addr(
    id: int,
    *,
    user_id: int = 1,
    name: str = "王小悦",
    is_default: bool = False,
    deleted: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        user_id=user_id,
        name=name,
        phone="13812345678",
        province="上海市",
        city="上海市",
        district="浦东新区",
        detail="张江高科技园区 1 号楼 501 室",
        is_default=is_default,
        deleted=deleted,
        created_at=None,
    )


class FakeDb:
    """内存 Session：仅支持 commit。"""

    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class FakeAddressRepo:
    """内存地址仓储：基于列表模拟全部仓储方法（id 即创建顺序）。"""

    def __init__(self) -> None:
        self.rows: list[SimpleNamespace] = []
        self._next_id = 1

    def list_by_user(self, user_id: int) -> list[SimpleNamespace]:
        rows = [r for r in self.rows if r.user_id == user_id and not r.deleted]
        return sorted(rows, key=lambda r: (not r.is_default, -r.id))

    def get_owned(self, user_id: int, address_id: int) -> SimpleNamespace | None:
        return next(
            (
                r
                for r in self.rows
                if r.id == address_id and r.user_id == user_id and not r.deleted
            ),
            None,
        )

    def count_by_user(self, user_id: int) -> int:
        return len([r for r in self.rows if r.user_id == user_id and not r.deleted])

    def clear_default(self, user_id: int) -> None:
        for r in self.rows:
            if r.user_id == user_id:
                r.is_default = False

    def latest(self, user_id: int) -> SimpleNamespace | None:
        rows = [r for r in self.rows if r.user_id == user_id and not r.deleted]
        return max(rows, key=lambda r: r.id) if rows else None

    def save(self, obj: SimpleNamespace) -> SimpleNamespace:
        if getattr(obj, "id", 0):
            for i, r in enumerate(self.rows):
                if r.id == obj.id:
                    self.rows[i] = obj
                    return obj
        obj.id = self._next_id
        self._next_id += 1
        self.rows.append(obj)
        return obj


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> tuple[FakeDb, FakeAddressRepo]:
    db = FakeDb()
    repo = FakeAddressRepo()
    # service 内部每次 AddressRepository(db) 都返回同一个内存 repo，保证状态跨调用共享
    monkeypatch.setattr(service, "AddressRepository", lambda d: repo)  # type: ignore[misc]
    return db, repo


# B4-1 新增合法参数：成功；首条自动置为默认
def test_create_first_auto_default(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    out = service.create_address(db, 1, _req())
    assert out["isDefault"] is True
    assert out["regionText"] == "上海市 上海市 浦东新区"


def test_create_second_not_default_by_default(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1, is_default=True)]
    out = service.create_address(db, 1, _req(name="李雷"))
    assert out["isDefault"] is False
    assert repo.rows[0].is_default is True  # 原默认保持


def test_create_is_default_clears_others(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1, is_default=True)]
    out = service.create_address(db, 1, _req(name="李雷", is_default=True))
    assert out["isDefault"] is True
    assert repo.rows[0].is_default is False  # 唯一默认


# B4-2 地址上限：已 20 条再新增 → 1301
def test_create_exceeds_limit(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(i) for i in range(1, ADDRESS_MAX_COUNT + 1)]
    with pytest.raises(BizException) as exc:
        service.create_address(db, 1, _req())
    assert exc.value.code == 1301
    assert exc.value.data == {"maxCount": ADDRESS_MAX_COUNT}


# B4-3 地址参数非法：缺必填字段 → 400
@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "  "},
        {"phone": "12345"},
        {"province": ""},
        {"detail": "  "},
    ],
)
def test_create_invalid_params(
    env: tuple[FakeDb, FakeAddressRepo], overrides: dict[str, object]
) -> None:
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.create_address(db, 1, _req(**overrides))
    assert exc.value.code == 400


# B4-4 设默认唯一：设多条为默认，仅 1 条 true
def test_set_default_unique(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1, is_default=True), _addr(2)]
    result = service.set_default(db, 1, 2)
    flags = {a["id"]: a["isDefault"] for a in result["list"]}
    assert flags == {1: False, 2: True}


def test_update_default_flag_unique(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1, is_default=True), _addr(2)]
    out = service.update_address(db, 1, 2, _req(name="李雷", is_default=True))
    assert out["isDefault"] is True
    assert repo.rows[0].is_default is False


# B4-5 删默认转移：删除默认地址后，剩余最新一条自动设为默认
def test_delete_default_transfers(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1, is_default=True), _addr(2)]
    result = service.delete_address(db, 1, 1)
    assert [a["id"] for a in result["list"]] == [2]
    assert result["list"][0]["isDefault"] is True  # 最新一条接任默认


def test_delete_non_default_keeps_default(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1, is_default=True), _addr(2)]
    result = service.delete_address(db, 1, 2)
    assert result["list"][0]["id"] == 1
    assert result["list"][0]["isDefault"] is True


# B4-6 地址不存在：操作不存在 id → 404
def test_update_not_found(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.update_address(db, 1, 999, _req())
    assert exc.value.code == 404


def test_delete_not_found(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.delete_address(db, 1, 999)
    assert exc.value.code == 404


def test_set_default_not_found(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    with pytest.raises(BizException) as exc:
        service.set_default(db, 1, 999)
    assert exc.value.code == 404


def test_cross_user_ownership(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1, user_id=2, is_default=True)]
    with pytest.raises(BizException) as exc:
        service.delete_address(db, 1, 1)  # 用户 1 操作用户 2 的地址
    assert exc.value.code == 404


# 列表排序：默认优先、创建倒序（id 即创建顺序）
def test_list_ordered(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1), _addr(2, is_default=True), _addr(3)]
    result = service.list_addresses(db, 1)
    ids = [a["id"] for a in result["list"]]
    assert ids == [2, 3, 1]  # 默认优先，其余按创建倒序


# 软删除：deleted 地址不展示
def test_deleted_hidden(env: tuple[FakeDb, FakeAddressRepo]) -> None:
    db, repo = env
    repo.rows = [_addr(1, is_default=True, deleted=True), _addr(2)]
    result = service.list_addresses(db, 1)
    assert [a["id"] for a in result["list"]] == [2]
