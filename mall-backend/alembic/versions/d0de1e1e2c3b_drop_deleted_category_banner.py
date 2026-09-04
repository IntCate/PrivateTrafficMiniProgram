"""drop deleted from category and banner

Revision ID: d0de1e1e2c3b
Revises: 8a5b3d4e2c1f
Create Date: 2026-09-04 10:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = 'd0de1e1e2c3b'
down_revision = '8a5b3d4e2c1f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """移除 category/banner 冗余的 deleted 列（随基类拆分：二者本就以 status 软开关）。"""
    op.drop_column('category', 'deleted')
    op.drop_column('banner', 'deleted')


def downgrade() -> None:
    op.add_column(
        'category',
        sa.Column('deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        'banner',
        sa.Column('deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
    )