"""add shipping_address table

Revision ID: 196b71a15a06
Revises: 0cc534ddac2d
Create Date: 2026-09-02 11:47:05.657016
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "196b71a15a06"
down_revision = "0cc534ddac2d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建收货地址表，对齐 docs/sql/schema.sql §3.6：含软删除列，idx_user_default + idx_user_deleted。"""
    op.create_table(
        "shipping_address",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="会员 ID"),
        sa.Column("name", sa.String(length=32), nullable=False, comment="收货人姓名"),
        sa.Column("phone", sa.String(length=20), nullable=False, comment="手机号"),
        sa.Column("province", sa.String(length=32), nullable=False, comment="省"),
        sa.Column("city", sa.String(length=32), nullable=False, comment="市"),
        sa.Column("district", sa.String(length=32), nullable=False, comment="区"),
        sa.Column("detail", sa.String(length=255), nullable=False, comment="详细地址"),
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
            comment="是否默认 1/0",
        ),
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
        sa.ForeignKeyConstraint(["user_id"], ["member.id"], name="fk_address_user"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_default", "shipping_address", ["user_id", "is_default"], unique=False)
    op.create_index("idx_user_deleted", "shipping_address", ["user_id", "deleted"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_user_deleted", table_name="shipping_address")
    op.drop_index("idx_user_default", table_name="shipping_address")
    op.drop_table("shipping_address")
