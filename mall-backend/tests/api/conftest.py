"""API 集成测试公共夹具：真实 MySQL 测试库 + 覆盖 get_db + 种子数据。

走真实 FastAPI 路由与鉴权（require_roles / get_current_admin），
使用独立 MySQL 测试库 `mall_admin_test`（不污染开发库 `mall`），
与生产同方言，避免 SQLite 差异。对齐 docs/api-design.md §13 与 auth.md §2。

性能策略：schema 只在 session 级别建表一次；每个测试只清空业务数据再重插
种子（种子均显式指定主键 id，不依赖自增），避免逐测试 drop/create 全库。
"""
from __future__ import annotations

from collections.abc import Generator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import get_db
from app.core.models import Base
from app.core.security import hash_password
from app.main import app
from app.modules.admin.models import AdminUser, SysConfig
from app.modules.after_sale.models import AfterSale
from app.modules.auth.models import Member
from app.modules.coupon.models import Coupon
from app.modules.order.models import Order
from app.modules.product.models import Banner, Category, Product

TEST_DB_URL = (
    "mysql+pymysql://test:123456@127.0.0.1:3306/mall_admin_test?charset=utf8mb4"
)


def _seed_base() -> list[Any]:
    """无外键依赖的表：admin/配置/分类/商品/会员/运营位/优惠券。"""
    return [
        AdminUser(
            id=1,
            username="admin",
            password=hash_password("Admin@123456"),
            nickname="超级管理员",
            role="admin",
            status=1,
        ),
        AdminUser(
            id=2,
            username="operator",
            password=hash_password("123456"),
            nickname="运营",
            role="operator",
            status=1,
        ),
        AdminUser(
            id=3,
            username="finance",
            password=hash_password("123456"),
            nickname="财务",
            role="finance",
            status=1,
        ),
        SysConfig(
            id=1,
            config_key="order_timeout_seconds",
            config_value="7200",
            remark="订单超时秒数",
        ),
        Category(
            id=1,
            parent_id=0,
            name="数码",
            icon="https://img.example.com/c.png",
            sort=0,
            status=1,
        ),
        Category(
            id=2,
            parent_id=0,
            name="服饰",
            icon="https://img.example.com/c2.png",
            sort=1,
            status=1,
        ),
        Product(
            id=1,
            product_no="P0001",
            category_id=1,
            brand="品牌",
            name="测试商品",
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
            status=1,
            views=5,
        ),
        Member(
            id=1,
            openid="mock_openid_1",
            nickname="测试会员",
            phone="13800000000",
            member_level="bronze",
            points=100,
            status=1,
        ),
        Banner(
            id=1,
            position="hero",
            title="主横幅",
            sub_title="副标题",
            image="https://img.example.com/b.png",
            link_type="none",
            sort=0,
            status=1,
        ),
        Coupon(
            id=1,
            name="满减券",
            type="cash",
            amount=Decimal("10.00"),
            min_amount=Decimal("50.00"),
            total_count=100,
            received_count=0,
            status=1,
        ),
    ]


def _seed_order() -> list[Any]:
    """依赖会员/商品的订单。"""
    return [
        Order(
            id=1,
            order_no="K0000000001",
            user_id=1,
            status="paid",
            total_amount=Decimal("100.00"),
            freight=Decimal("0.00"),
            pay_amount=Decimal("100.00"),
            coupon_amount=Decimal("0.00"),
            points_used=0,
            receiver_name="张三",
            receiver_phone="13800000000",
            receiver_region="上海市 浦东新区",
            receiver_detail="xx路1号",
            pay_type="mock",
        ),
        Order(
            id=2,
            order_no="K0000000002",
            user_id=1,
            status="pending",
            total_amount=Decimal("50.00"),
            freight=Decimal("0.00"),
            pay_amount=Decimal("50.00"),
            coupon_amount=Decimal("0.00"),
            points_used=0,
            receiver_name="张三",
            receiver_phone="13800000000",
            receiver_region="上海市 浦东新区",
            receiver_detail="xx路1号",
            pay_type="mock",
        ),
    ]


def _seed_after_sale() -> list[Any]:
    """依赖订单的售后工单。"""
    return [
        AfterSale(
            id=1,
            order_id=1,
            user_id=1,
            type="refund",
            reason="商品破损",
            amount=Decimal("100.00"),
            status="applying",
        )
    ]


@pytest.fixture(scope="session")
def _engine() -> Any:
    """session 级引擎：整个测试会话只建表一次。"""
    engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        Base.metadata.drop_all(conn)
        Base.metadata.create_all(conn)
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(_engine: Any) -> Generator[Session, None, None]:
    """function 级会话：清空业务数据后重插种子，供单个测试使用。"""
    with _engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    testing_session = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    session = testing_session()
    session.add_all(_seed_base())
    session.flush()
    session.add_all(_seed_order())
    session.flush()
    session.add_all(_seed_after_sale())
    session.commit()
    yield session
    session.close()


@pytest.fixture
def client(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    """TestClient：覆盖 get_db 指向 MySQL 测试库，屏蔽调度器启动。"""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.main.init_scheduler", lambda: None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
