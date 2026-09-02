"""add orders and order_item tables

Revision ID: 7f3a1c2d9b4e
Revises: 196b71a15a06
Create Date: 2026-09-02 15:30:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "7f3a1c2d9b4e"
down_revision = "196b71a15a06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建订单主表与明细表，对齐 docs/sql/schema.sql §3.7/§3.8。"""
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "order_no",
            sa.String(length=32),
            nullable=False,
            comment="订单号 K+时间戳+3位随机",
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="会员 ID"),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
            comment="pending/paid/shipped/completed/refund/cancelled",
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(10, 2),
            server_default=sa.text("0.00"),
            nullable=False,
            comment="商品总金额",
        ),
        sa.Column(
            "freight",
            sa.Numeric(10, 2),
            server_default=sa.text("0.00"),
            nullable=False,
            comment="运费",
        ),
        sa.Column(
            "pay_amount",
            sa.Numeric(10, 2),
            server_default=sa.text("0.00"),
            nullable=False,
            comment="实付金额",
        ),
        sa.Column(
            "coupon_amount",
            sa.Numeric(10, 2),
            server_default=sa.text("0.00"),
            nullable=False,
            comment="优惠券抵扣",
        ),
        sa.Column(
            "points_used",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="积分抵扣",
        ),
        sa.Column("receiver_name", sa.String(length=32), nullable=False, comment="收货人快照"),
        sa.Column("receiver_phone", sa.String(length=20), nullable=False, comment="收货电话快照"),
        sa.Column("receiver_region", sa.String(length=128), nullable=False, comment="省市区快照"),
        sa.Column("receiver_detail", sa.String(length=255), nullable=False, comment="详细地址快照"),
        sa.Column("pay_type", sa.String(length=20), nullable=True, comment="wechat/mock"),
        sa.Column("transaction_id", sa.String(length=64), nullable=True, comment="微信支付单号"),
        sa.Column("remark", sa.String(length=255), nullable=True, comment="买家备注"),
        sa.Column("cancel_reason", sa.String(length=255), nullable=True, comment="取消/关闭原因"),
        sa.Column("refund_reason", sa.String(length=255), nullable=True, comment="售后/退款原因"),
        sa.Column(
            "refund_type",
            sa.String(length=20),
            nullable=True,
            comment="refund 仅退款 / return 退货退款",
        ),
        sa.Column("refund_time", sa.DateTime(), nullable=True, comment="申请售后时间"),
        sa.Column("pay_time", sa.DateTime(), nullable=True, comment="支付时间"),
        sa.Column("ship_time", sa.DateTime(), nullable=True, comment="发货时间"),
        sa.Column("finish_time", sa.DateTime(), nullable=True, comment="完成时间"),
        sa.Column(
            "deleted",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
            comment="逻辑删除",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["member.id"], name="fk_order_user"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no", name="uk_order_no"),
    )
    op.create_index(
        "idx_user_status", "orders", ["user_id", "status", "created_at"], unique=False
    )
    op.create_index("idx_status", "orders", ["status", "created_at"], unique=False)

    op.create_table(
        "order_item",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False, comment="订单 ID"),
        sa.Column("product_id", sa.BigInteger(), nullable=False, comment="商品 ID"),
        sa.Column("sku_id", sa.BigInteger(), nullable=False, comment="SKU ID"),
        sa.Column("product_name", sa.String(length=128), nullable=False, comment="商品名快照"),
        sa.Column("sku_text", sa.String(length=128), nullable=False, comment="SKU 文案快照"),
        sa.Column("image", sa.String(length=512), nullable=False, comment="主图快照"),
        sa.Column(
            "price",
            sa.Numeric(10, 2),
            server_default=sa.text("0.00"),
            nullable=False,
            comment="成交单价快照",
        ),
        sa.Column(
            "quantity", sa.Integer(), server_default=sa.text("0"), nullable=False, comment="数量"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_orderitem_order"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_order", "order_item", ["order_id"], unique=False)
    op.create_index("idx_product", "order_item", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_product", table_name="order_item")
    op.drop_index("idx_order", table_name="order_item")
    op.drop_table("order_item")
    op.drop_index("idx_status", table_name="orders")
    op.drop_index("idx_user_status", table_name="orders")
    op.drop_table("orders")
