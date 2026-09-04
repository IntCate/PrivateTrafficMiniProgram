"""add coupon, user_coupon and points_log tables

Revision ID: a1b2c3d4e5f6
Revises: d0de1e1e2c3b
Create Date: 2026-09-04 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "d0de1e1e2c3b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建优惠券模板、用户优惠券、积分明细表，对齐 docs/database-design.md §3.10/§3.11/§3.12。"""
    op.create_table(
        "coupon",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False, comment="券名称"),
        sa.Column(
            "type",
            sa.String(length=20),
            server_default=sa.text("'cash'"),
            nullable=False,
            comment="cash 满减 / discount 折扣 / shipping 免运费",
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=True, comment="满减金额（cash 用）"),
        sa.Column("discount", sa.Numeric(4, 2), nullable=True, comment="折扣（discount 用，如 0.85）"),
        sa.Column(
            "min_amount",
            sa.Numeric(10, 2),
            server_default=sa.text("0.00"),
            nullable=False,
            comment="使用门槛",
        ),
        sa.Column(
            "total_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="发放总量，0 不限",
        ),
        sa.Column(
            "received_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="已领取数量",
        ),
        sa.Column("valid_start", sa.DateTime(), nullable=True, comment="生效时间"),
        sa.Column("valid_end", sa.DateTime(), nullable=True, comment="失效时间"),
        sa.Column(
            "status",
            sa.SmallInteger(),
            server_default=sa.text("1"),
            nullable=False,
            comment="1 启用 / 0 停用",
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_coupon",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="会员 ID"),
        sa.Column("coupon_id", sa.BigInteger(), nullable=False, comment="券模板 ID"),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'unused'"),
            nullable=False,
            comment="unused 未使用 / used 已使用 / expired 已过期",
        ),
        sa.Column("used_order_no", sa.String(length=32), nullable=True, comment="核销订单号"),
        sa.Column("used_at", sa.DateTime(), nullable=True, comment="使用时间"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.ForeignKeyConstraint(["coupon_id"], ["coupon.id"], name="fk_usercoupon_coupon"),
        sa.ForeignKeyConstraint(["user_id"], ["member.id"], name="fk_usercoupon_member"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_status", "user_coupon", ["user_id", "status"], unique=False)

    op.create_table(
        "points_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="会员 ID"),
        sa.Column(
            "change",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="变动值（正增负减）",
        ),
        sa.Column(
            "balance",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="变动后余额",
        ),
        sa.Column(
            "type",
            sa.String(length=20),
            nullable=False,
            comment="earn 获得 / consume 消费 / refund 退回",
        ),
        sa.Column(
            "biz_type",
            sa.String(length=32),
            nullable=False,
            comment="业务场景：order/promotion/admin",
        ),
        sa.Column("remark", sa.String(length=255), nullable=True, comment="说明"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["member.id"], name="fk_pointlog_member"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user", "points_log", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_user", table_name="points_log")
    op.drop_table("points_log")
    op.drop_index("idx_user_status", table_name="user_coupon")
    op.drop_table("user_coupon")
    op.drop_table("coupon")
