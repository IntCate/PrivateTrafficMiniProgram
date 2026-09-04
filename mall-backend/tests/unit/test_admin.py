"""后台管理模块单元测试：登录、管理员、商品、分类、订单、会员、运营位、优惠券、售后、数据概览、系统配置。

对齐 docs/api-design.md §13 与 auth.md §2 权限矩阵。使用内存 Fake 仓储/桩验证 service 业务分支。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.exceptions import BizException
from app.modules.admin import service
from app.modules.admin.models import AdminUser, SysConfig
from app.modules.admin.schemas import (
    CreateAdminRequest,
    CreateBannerRequest,
    CreateCategoryRequest,
    CreateCouponRequest,
    CreateProductRequest,
    GrantCouponRequest,
    ShipOrderRequest,
    UpdateAdminStatusRequest,
    UpdateConfigRequest,
    UpdateMemberStatusRequest,
    UpdateProductStatusRequest,
)
from app.modules.after_sale.models import AfterSale
from app.modules.auth.models import Member
from app.modules.coupon.models import Coupon
from app.modules.order.models import Order
from app.modules.product.models import Banner, Category, Product


def _admin(
    id: int,
    *,
    username: str = "admin",
    password: str = "hashed",
    nickname: str | None = "管理员",
    role: str = "admin",
    status: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        username=username,
        password=password,
        nickname=nickname,
        role=role,
        status=status,
        last_login_at=None,
        created_at=datetime(2026, 9, 1, 10, 0, 0),
    )


def _product(id: int, *, name: str = "商品", status: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        product_no=f"P{id:04d}",
        category_id=1,
        brand="品牌",
        name=name,
        sub_title="副标题",
        price=Decimal("99.00"),
        original_price=Decimal("129.00"),
        main_image="https://img.example.com/p.png",
        images=["https://img.example.com/p1.png"],
        detail_html="<p>详情</p>",
        spec={"颜色": "黑"},
        sales=10,
        stock=100,
        tags=["热销"],
        shipping_from="上海",
        is_free_shipping=True,
        status=status,
        views=5,
        deleted=False,
        created_at=datetime(2026, 9, 1, 10, 0, 0),
    )


def _category(id: int, *, name: str = "分类", status: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        parent_id=0,
        name=name,
        icon="https://img.example.com/c.png",
        sort=0,
        status=status,
    )


def _order(
    id: int,
    *,
    user_id: int = 1,
    status: str = "paid",
    pay_amount: str = "100.00",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        order_no=f"K{id:010d}",
        user_id=user_id,
        status=status,
        total_amount=Decimal("100.00"),
        freight=Decimal("0.00"),
        pay_amount=Decimal(pay_amount),
        coupon_amount=Decimal("0.00"),
        points_used=0,
        receiver_name="张三",
        receiver_phone="13800000000",
        receiver_region="上海市 浦东新区",
        receiver_detail="xx路1号",
        pay_type="mock",
        transaction_id=None,
        remark=None,
        cancel_reason=None,
        refund_reason=None,
        created_at=datetime(2026, 9, 1, 10, 0, 0),
    )


def _member(id: int, *, nickname: str = "会员", status: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        nickname=nickname,
        phone="13800000000",
        member_level="bronze",
        points=100,
        status=status,
        deleted=False,
        created_at=datetime(2026, 9, 1, 10, 0, 0),
    )


def _banner(id: int, *, position: str = "hero", status: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        position=position,
        title="主横幅",
        sub_title="副标题",
        image="https://img.example.com/b.png",
        link_type="none",
        link_value=None,
        sort=0,
        status=status,
    )


def _coupon(id: int, *, name: str = "满减券", status: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        name=name,
        type="cash",
        amount=Decimal("10.00"),
        discount=None,
        min_amount=Decimal("50.00"),
        total_count=100,
        received_count=0,
        valid_start=None,
        valid_end=None,
        status=status,
    )


def _after_sale(
    id: int, *, order_id: int = 1, status: str = "applying"
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        order_id=order_id,
        user_id=1,
        type="refund",
        reason="商品破损",
        amount=Decimal("100.00"),
        status=status,
        audit_remark=None,
        created_at=datetime(2026, 9, 1, 10, 0, 0),
    )


def _config(key: str, value: str, remark: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        config_key=key,
        config_value=value,
        remark=remark,
    )


_MODEL_BY_TABLE = {
    m.__tablename__: m
    for m in (AdminUser, SysConfig, Product, Category, Order, Member, Banner, Coupon, AfterSale)
}

_MODEL_BY_NAME = {m.__name__: m for m in _MODEL_BY_TABLE.values()}

_DEFAULTS: dict[type, dict[str, object]] = {
    Product: {"sales": 0, "views": 0, "stock": 0, "status": 1, "is_free_shipping": True},
    Coupon: {"received_count": 0, "total_count": 0, "min_amount": Decimal("0.00")},
    Category: {"parent_id": 0, "sort": 0, "status": 1},
    Banner: {"sort": 0, "status": 1, "link_type": "none"},
    AdminUser: {"status": 1, "role": "admin"},
    Member: {"status": 1, "points": 0, "member_level": "bronze"},
    AfterSale: {"status": "applying", "amount": Decimal("0.00")},
}


def _model_from_stmt(stmt: object) -> type | None:
    try:
        for d in stmt.column_descriptions:  # type: ignore[attr-defined]
            ent = d.get("entity")
            if isinstance(ent, type):
                return ent
    except Exception:
        pass
    for f in stmt.froms:  # type: ignore[attr-defined]
        name = getattr(f, "name", None)
        if name in _MODEL_BY_TABLE:
            return _MODEL_BY_TABLE[name]
    return None


class FakeDb:
    """内存 Session：支持 get/scalar/scalars/add/flush/commit/delete。"""

    def __init__(self, **models: list[SimpleNamespace]) -> None:
        self._data: dict[type, dict[int, SimpleNamespace]] = {}
        for name, rows in models.items():
            model = _MODEL_BY_NAME[name]
            self._data[model] = {r.id: r for r in rows}
        self._pending: list[object] = []
        self._next_id = 100
        self.commits = 0
        self._sums: dict[type, Decimal] = {}

    def get(self, model: type, pk: int) -> object | None:
        return self._data.get(model, {}).get(pk)

    def scalar(self, stmt: object) -> object:
        model = _model_from_stmt(stmt)
        if model is None:
            return 0
        s = str(stmt).lower()
        if "sum(" in s or "coalesce" in s:
            return self._sums.get(model, Decimal("0.00"))
        return len(self._data.get(model, {}))
    def scalars(self, stmt: object) -> list[SimpleNamespace]:
        model = _model_from_stmt(stmt)
        rows = sorted(self._data.get(model, {}).values(), key=lambda r: r.id)
        return rows

    def add(self, obj: object) -> None:
        self._pending.append(obj)

    def flush(self) -> None:
        for obj in self._pending:
            model = type(obj)
            if getattr(obj, "id", None) is None:
                obj.id = self._next_id  # type: ignore[attr-defined]
                self._next_id += 1
            if not hasattr(obj, "created_at") or obj.created_at is None:
                obj.created_at = datetime(2026, 9, 1, 10, 0, 0)  # type: ignore[attr-defined]
            for field, default in _DEFAULTS.get(model, {}).items():
                if getattr(obj, field, None) is None:
                    setattr(obj, field, default)
            self._data.setdefault(model, {})[obj.id] = obj  # type: ignore[attr-defined]
        self._pending = []

    def commit(self) -> None:
        self.flush()
        self.commits += 1

    def delete(self, obj: object) -> None:
        for _model, rows in self._data.items():
            for pk, row in list(rows.items()):
                if row is obj:
                    del rows[pk]
                    return


class FakeAdminUserRepo:
    """内存管理员仓储。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db

    def get_by_username(self, username: str) -> SimpleNamespace | None:
        for a in self.db._data.get(AdminUser, {}).values():
            if a.username == username:
                return a
        return None

    def page_admins(
        self, page: int, page_size: int
    ) -> tuple[list[SimpleNamespace], int]:
        rows = sorted(self.db._data.get(AdminUser, {}).values(), key=lambda a: a.id)
        total = len(rows)
        start = (page - 1) * page_size
        return rows[start : start + page_size], total

    def save(self, obj: object) -> object:
        self.db.add(obj)
        self.db.flush()
        return obj


class FakeSysConfigRepo:
    """内存系统配置仓储。"""

    def __init__(self, db: FakeDb) -> None:
        self.db = db

    def get_by_key(self, key: str) -> SimpleNamespace | None:
        for c in self.db._data.get(SysConfig, {}).values():
            if c.config_key == key:
                return c
        return None

    def list_all(self) -> list[SimpleNamespace]:
        return sorted(self.db._data.get(SysConfig, {}).values(), key=lambda c: c.id)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> FakeDb:
    db = FakeDb(
        AdminUser=[_admin(1)],
        Product=[_product(1), _product(2)],
        Category=[_category(1)],
        Order=[_order(1), _order(2, status="pending")],
        Member=[_member(1)],
        Banner=[_banner(1)],
        Coupon=[_coupon(1)],
        AfterSale=[_after_sale(1)],
        SysConfig=[_config("order_timeout_seconds", "7200")],
    )
    monkeypatch.setattr(service, "AdminUserRepository", lambda d: FakeAdminUserRepo(d))
    monkeypatch.setattr(service, "SysConfigRepository", lambda d: FakeSysConfigRepo(d))
    monkeypatch.setattr(service, "verify_password", lambda p, h: True)
    monkeypatch.setattr(service, "create_admin_jwt", lambda aid, role: "token")
    monkeypatch.setattr(service, "hash_password", lambda p: "hashed")
    return db


# ---- 登录 ----

def test_login_ok(env: FakeDb) -> None:
    out = service.login(env, "admin", "Admin@123456")
    assert out.token == "token"
    assert out.admin.username == "admin"
    assert out.admin.role == "admin"


def test_login_wrong_password(env: FakeDb, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "verify_password", lambda p, h: False)
    with pytest.raises(BizException) as e:
        service.login(env, "admin", "wrong")
    assert e.value.code == 1701


def test_login_disabled(env: FakeDb) -> None:
    env._data[AdminUser][1].status = 0
    with pytest.raises(BizException) as e:
        service.login(env, "admin", "Admin@123456")
    assert e.value.code == 1701


def test_login_not_found(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.login(env, "nobody", "x")
    assert e.value.code == 1701


# ---- 管理员 ----

def test_list_admins_ok(env: FakeDb) -> None:
    data = service.list_admins(env, 1, 10)
    assert data["total"] == 1
    assert data["list"][0]["username"] == "admin"
    assert data["hasMore"] is False


def test_create_admin_ok(env: FakeDb) -> None:
    body = CreateAdminRequest(username="op1", password="123456", role="operator")
    out = service.create_admin(env, body)
    assert out.username == "op1"
    assert out.role == "operator"
    assert env._data[AdminUser][100].password == "hashed"


def test_create_admin_duplicate(env: FakeDb) -> None:
    body = CreateAdminRequest(username="admin", password="123456")
    with pytest.raises(BizException) as e:
        service.create_admin(env, body)
    assert e.value.code == 1702


def test_update_admin_status_ok(env: FakeDb) -> None:
    body = UpdateAdminStatusRequest(status=0)
    out = service.update_admin_status(env, 1, body, current_admin_id=2)
    assert out.status == 0


def test_update_admin_status_not_found(env: FakeDb) -> None:
    body = UpdateAdminStatusRequest(status=0)
    with pytest.raises(BizException) as e:
        service.update_admin_status(env, 999, body, current_admin_id=2)
    assert e.value.code == 404


def test_update_admin_status_self_disable(env: FakeDb) -> None:
    body = UpdateAdminStatusRequest(status=0)
    with pytest.raises(BizException) as e:
        service.update_admin_status(env, 1, body, current_admin_id=1)
    assert e.value.code == 1703


# ---- 商品 ----

def test_list_products_ok(env: FakeDb) -> None:
    data = service.list_products(env, 1, 10)
    assert data["total"] == 2
    assert data["list"][0]["name"] == "商品"


def test_get_product_ok(env: FakeDb) -> None:
    out = service.get_product(env, 1)
    assert out.id == 1
    assert out.price == Decimal("99.00")


def test_get_product_not_found(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.get_product(env, 999)
    assert e.value.code == 404


def test_create_product_ok(env: FakeDb) -> None:
    body = CreateProductRequest(
        product_no="P1000",
        category_id=1,
        name="新品",
        price=Decimal("9.90"),
        main_image="https://img.example.com/p.png",
    )
    out = service.create_product(env, body)
    assert out.id == 100
    assert out.name == "新品"


def test_create_product_category_not_found(env: FakeDb) -> None:
    body = CreateProductRequest(
        product_no="P1000",
        category_id=999,
        name="新品",
        price=Decimal("9.90"),
        main_image="https://img.example.com/p.png",
    )
    with pytest.raises(BizException) as e:
        service.create_product(env, body)
    assert e.value.code == 404


def test_update_product_status_ok(env: FakeDb) -> None:
    body = UpdateProductStatusRequest(status=0)
    out = service.update_product_status(env, 1, body)
    assert out.status == 0


def test_update_product_status_not_found(env: FakeDb) -> None:
    body = UpdateProductStatusRequest(status=0)
    with pytest.raises(BizException) as e:
        service.update_product_status(env, 999, body)
    assert e.value.code == 404


def test_delete_product_ok(env: FakeDb) -> None:
    service.delete_product(env, 1)
    assert env._data[Product][1].deleted is True


def test_delete_product_not_found(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.delete_product(env, 999)
    assert e.value.code == 404


# ---- 分类 ----

def test_list_categories_ok(env: FakeDb) -> None:
    data = service.list_categories(env)
    assert len(data) == 1
    assert data[0]["name"] == "分类"


def test_create_category_ok(env: FakeDb) -> None:
    body = CreateCategoryRequest(name="新分类")
    out = service.create_category(env, body)
    assert out["id"] == 100
    assert out["name"] == "新分类"


def test_update_category_not_found(env: FakeDb) -> None:
    from app.modules.admin.schemas import UpdateCategoryRequest

    body = UpdateCategoryRequest(name="改名")
    with pytest.raises(BizException) as e:
        service.update_category(env, 999, body)
    assert e.value.code == 404


def test_delete_category_ok(env: FakeDb) -> None:
    service.delete_category(env, 1)
    assert 1 not in env._data[Category]


# ---- 订单 ----

def test_list_orders_ok(env: FakeDb) -> None:
    data = service.list_orders(env, 1, 10)
    assert data["total"] == 2


def test_get_order_ok(env: FakeDb) -> None:
    out = service.get_order(env, 1)
    assert out.order_no == "K0000000001"


def test_get_order_not_found(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.get_order(env, 999)
    assert e.value.code == 404


def test_ship_order_ok(env: FakeDb) -> None:
    body = ShipOrderRequest(tracking_no="SF123")
    out = service.ship_order(env, 1, body)
    assert out.status == "shipped"


def test_ship_order_wrong_status(env: FakeDb) -> None:
    body = ShipOrderRequest()
    with pytest.raises(BizException) as e:
        service.ship_order(env, 2, body)
    assert e.value.code == 1402


def test_ship_order_not_found(env: FakeDb) -> None:
    body = ShipOrderRequest()
    with pytest.raises(BizException) as e:
        service.ship_order(env, 999, body)
    assert e.value.code == 404


# ---- 会员 ----

def test_list_members_ok(env: FakeDb) -> None:
    data = service.list_members(env, 1, 10)
    assert data["total"] == 1
    assert data["list"][0]["nickname"] == "会员"


def test_update_member_status_ok(env: FakeDb) -> None:
    body = UpdateMemberStatusRequest(status=0)
    out = service.update_member_status(env, 1, body)
    assert out["status"] == 0


def test_update_member_status_not_found(env: FakeDb) -> None:
    body = UpdateMemberStatusRequest(status=0)
    with pytest.raises(BizException) as e:
        service.update_member_status(env, 999, body)
    assert e.value.code == 404


# ---- 运营位 ----

def test_list_banners_ok(env: FakeDb) -> None:
    data = service.list_banners(env)
    assert len(data) == 1
    assert data[0]["title"] == "主横幅"


def test_create_banner_ok(env: FakeDb) -> None:
    body = CreateBannerRequest(position="hero", title="新横幅", image="https://img.example.com/x.png")
    out = service.create_banner(env, body)
    assert out["id"] == 100
    assert out["title"] == "新横幅"


def test_delete_banner_ok(env: FakeDb) -> None:
    service.delete_banner(env, 1)
    assert 1 not in env._data[Banner]


# ---- 优惠券 ----

def test_list_coupons_ok(env: FakeDb) -> None:
    data = service.list_coupons(env)
    assert len(data) == 1
    assert data[0]["name"] == "满减券"


def test_create_coupon_ok(env: FakeDb) -> None:
    body = CreateCouponRequest(name="新券", type="cash", amount=Decimal("5.00"))
    out = service.create_coupon(env, body)
    assert out["id"] == 100
    assert out["name"] == "新券"


def test_grant_coupon_ok(env: FakeDb) -> None:
    body = GrantCouponRequest(user_id=1, count=2)
    out = service.grant_coupon(env, 1, body)
    assert out["granted"] == 2
    assert env._data[Coupon][1].received_count == 2


def test_grant_coupon_coupon_not_found(env: FakeDb) -> None:
    body = GrantCouponRequest(user_id=1, count=1)
    with pytest.raises(BizException) as e:
        service.grant_coupon(env, 999, body)
    assert e.value.code == 404


def test_grant_coupon_member_not_found(env: FakeDb) -> None:
    body = GrantCouponRequest(user_id=999, count=1)
    with pytest.raises(BizException) as e:
        service.grant_coupon(env, 1, body)
    assert e.value.code == 404


# ---- 售后 ----

def test_list_after_sales_ok(env: FakeDb) -> None:
    data = service.list_after_sales(env, 1, 10)
    assert data["total"] == 1


def test_audit_after_sale_ok(env: FakeDb) -> None:
    out = service.audit_after_sale(env, 1, approve=True, remark="同意")
    assert out["status"] == "approved"
    assert out["audit_remark"] == "同意"


def test_audit_after_sale_reject(env: FakeDb) -> None:
    out = service.audit_after_sale(env, 1, approve=False, remark="驳回")
    assert out["status"] == "rejected"


def test_audit_after_sale_wrong_status(env: FakeDb) -> None:
    env._data[AfterSale][1].status = "approved"
    with pytest.raises(BizException) as e:
        service.audit_after_sale(env, 1, approve=True)
    assert e.value.code == 1402


def test_audit_after_sale_not_found(env: FakeDb) -> None:
    with pytest.raises(BizException) as e:
        service.audit_after_sale(env, 999, approve=True)
    assert e.value.code == 404


# ---- 数据概览 ----

def test_dashboard_summary_ok(env: FakeDb) -> None:
    env._sums[Order] = Decimal("100.00")
    out = service.dashboard_summary(env)
    assert out.total_sales == Decimal("100.00")
    assert out.order_count == 2
    assert out.member_count == 1
    assert out.product_count == 2


# ---- 系统配置 ----

def test_list_configs_ok(env: FakeDb) -> None:
    data = service.list_configs(env)
    assert len(data) == 1
    assert data[0]["config_key"] == "order_timeout_seconds"


def test_update_config_ok(env: FakeDb) -> None:
    body = UpdateConfigRequest(config_value="3600")
    out = service.update_config(env, "order_timeout_seconds", body)
    assert out["config_value"] == "3600"


def test_update_config_not_found(env: FakeDb) -> None:
    body = UpdateConfigRequest(config_value="3600")
    with pytest.raises(BizException) as e:
        service.update_config(env, "not_exist", body)
    assert e.value.code == 404
