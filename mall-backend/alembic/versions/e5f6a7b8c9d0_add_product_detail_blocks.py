"""add product detail_blocks column

Revision ID: e5f6a7b8c9d0
Revises: c3d4e5f6a7b8
Create Date: 2026-09-06 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """商品详情新增结构化区块字段 detail_blocks（JSON），兼容旧 detail_html。"""
    op.add_column(
        "product",
        sa.Column(
            "detail_blocks",
            sa.JSON(),
            nullable=True,
            comment="详情区块(JSON)：[{type:text|image, content/url}]",
        ),
    )


def downgrade() -> None:
    op.drop_column("product", "detail_blocks")
