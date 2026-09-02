"""add cart table

Revision ID: 0cc534ddac2d
Revises: 55fed9b222ea
Create Date: 2026-09-02 11:19:45.656807
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0cc534ddac2d"
down_revision = "55fed9b222ea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建购物车表，对齐 docs/sql/schema.sql：uk_user_sku + idx_user + 三外键，无软删除列。"""
    op.create_table(
        "cart",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="会员 ID"),
        sa.Column("product_id", sa.BigInteger(), nullable=False, comment="商品 ID"),
        sa.Column("sku_id", sa.BigInteger(), nullable=False, comment="SKU ID"),
        sa.Column("quantity", sa.Integer(), nullable=False, comment="数量"),
        sa.Column("selected", sa.Boolean(), nullable=False, comment="勾选 1/0"),
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
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], name="fk_cart_product"),
        sa.ForeignKeyConstraint(["sku_id"], ["product_sku.id"], name="fk_cart_sku"),
        sa.ForeignKeyConstraint(["user_id"], ["member.id"], name="fk_cart_user"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "sku_id", name="uk_user_sku"),
    )
    op.create_index("idx_user", "cart", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_user", table_name="cart")
    op.drop_table("cart")
