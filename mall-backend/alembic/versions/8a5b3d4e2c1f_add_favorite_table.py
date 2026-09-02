"""add favorite table

Revision ID: 8a5b3d4e2c1f
Revises: 7f3a1c2d9b4e
Create Date: 2026-09-02 16:30:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "8a5b3d4e2c1f"
down_revision = "7f3a1c2d9b4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建收藏表，对齐 docs/sql/schema.sql §3.9。"""
    op.create_table(
        "favorite",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="会员 ID"),
        sa.Column("product_id", sa.BigInteger(), nullable=False, comment="商品 ID"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["member.id"], name="fk_fav_user"),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], name="fk_fav_product"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uk_user_product"),
    )


def downgrade() -> None:
    op.drop_table("favorite")
