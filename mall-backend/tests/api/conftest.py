"""API 集成测试公共夹具：SQLite 内存库 + 覆盖 get_db + 种子数据。

走真实 FastAPI 路由与鉴权（require_roles / get_current_admin），
用内存 SQLite 替代 MySQL，避免污染开发库。对齐 docs/api-design.md §13 与 auth.md §2。
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, Integer, MetaData, create_engine, event
from sqlalchemy.orm import sessionmaker

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


@event.listens_for(Base.metadata, "before_create")
def _adapt_sqlite_schema(target: MetaData, connection: object, **kwargs: object) -> None:
    """适配 SQLite 方言差异（MySQL 兼容测试）。

    1. SQLite 索引名全局唯一，而项目存在跨表重名索引（如 idx_user_status），
       给每个索引名加表名前缀避免冲突；
    2. SQLite 仅 INTEGER PRIMARY KEY 自增，而项目主键为 BigInteger，
       将主键列改为 Integer 以支持自增。
    """
    for table in target.tables.values():
        for index in table.indexes:
            index.name = f"{table.name}_{index.name}"  # type: ignore[assignment]
        for column in table.columns:
            if column.primary_key and isinstance(column.type, BigInteger):
                column.type = Integer()


@pytest.fixture
def db_session(tmp_path: Path) -> object:
    """文件型 SQLite 会话（每测试独立文件），含后台各资源种子数据。"""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = testing_session()

    session.add_all(
        [
            AdminUser(
                username="admin",
                password=hash_password("Admin@123456"),
                nickname="超级管理员",
                role="admin",
                status=1,
            ),
            AdminUser(
                username="operator",
                password=hash_password("123456"),
                nickname="运营",
                role="operator",
                status=1,
            ),
            AdminUser(
                username="finance",
                password=hash_password("123456"),
                nickname="财务",
                role="finance",
                status=1,
            ),
            SysConfig(
                config_key="order_timeout_seconds",
                config_value="7200",
                remark="订单超时秒数",
            ),
            Category(
                parent_id=0,
                name="数码",
                icon="https://img.example.com/c.png",
                sort=0,
                status=1,
            ),
            Product(
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
                openid="mock_openid_1",
                nickname="测试会员",
                phone="13800000000",
                member_level="bronze",
                points=100,
                status=1,
            ),
            Order(
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
            Banner(
                position="hero",
                title="主横幅",
                sub_title="副标题",
                image="https://img.example.com/b.png",
                link_type="none",
                sort=0,
                status=1,
            ),
            Coupon(
                name="满减券",
                type="cash",
                amount=Decimal("10.00"),
                min_amount=Decimal("50.00"),
                total_count=100,
                received_count=0,
                status=1,
            ),
            AfterSale(
                order_id=1,
                user_id=1,
                type="refund",
                reason="商品破损",
                amount=Decimal("100.00"),
                status="applying",
            ),
        ]
    )
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db_session: object, monkeypatch: pytest.MonkeyPatch) -> object:
    """TestClient：覆盖 get_db 指向内存库，屏蔽调度器启动。"""

    def override_get_db() -> object:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.main.init_scheduler", lambda: None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
