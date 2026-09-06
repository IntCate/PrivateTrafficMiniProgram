"""drop product detail_html column

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-06 13:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """商品详情移除旧富文本字段 detail_html，仅保留结构化区块 detail_blocks。"""
    op.drop_column("product", "detail_html")


def downgrade() -> None:
    op.add_column(
        "product",
        sa.Column("detail_html", sa.Text(), nullable=True, comment="详情富文本"),
    )
