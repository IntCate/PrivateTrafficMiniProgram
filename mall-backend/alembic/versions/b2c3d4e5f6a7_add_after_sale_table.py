"""add after_sale table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-04 13:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建售后工单表，对齐 docs/database-design.md §3.14。"""
    op.create_table(
        "after_sale",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False, comment="订单 ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="会员 ID"),
        sa.Column(
            "type",
            sa.String(length=20),
            nullable=False,
            comment="refund 仅退款 / return 退货退款",
        ),
        sa.Column("reason", sa.String(length=255), nullable=False, comment="申请原因"),
        sa.Column(
            "amount",
            sa.Numeric(10, 2),
            server_default=sa.text("0.00"),
            nullable=False,
            comment="申请金额",
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'applying'"),
            nullable=False,
            comment="applying/approved/rejected/refunded/closed",
        ),
        sa.Column("images", sa.JSON(), nullable=True, comment="凭证图片"),
        sa.Column("audit_remark", sa.String(length=255), nullable=True, comment="审核意见"),
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
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_aftersale_order"),
        sa.ForeignKeyConstraint(["user_id"], ["member.id"], name="fk_aftersale_member"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_order", "after_sale", ["order_id"], unique=False)
    op.create_index("idx_user", "after_sale", ["user_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_user", table_name="after_sale")
    op.drop_index("idx_order", table_name="after_sale")
    op.drop_table("after_sale")
