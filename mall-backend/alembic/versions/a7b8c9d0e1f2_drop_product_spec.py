"""drop product spec column

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-07 10:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """商品移除参数规格字段 spec，规格信息并入商品详情区块 detail_blocks。"""
    op.drop_column("product", "spec")


def downgrade() -> None:
    op.add_column(
        "product",
        sa.Column("spec", sa.JSON(), nullable=True, comment="参数规格(JSON)"),
    )
