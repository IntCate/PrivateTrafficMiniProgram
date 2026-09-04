"""add admin_user and sys_config tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-04 14:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建管理员表与系统配置表，对齐 docs/database-design.md §3.15/§3.17。"""
    op.create_table(
        "admin_user",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=32), nullable=False, comment="登录名"),
        sa.Column("password", sa.String(length=128), nullable=False, comment="BCrypt 哈希"),
        sa.Column("nickname", sa.String(length=32), nullable=True, comment="姓名"),
        sa.Column(
            "role",
            sa.String(length=20),
            server_default=sa.text("'admin'"),
            nullable=False,
            comment="admin/operator/finance",
        ),
        sa.Column(
            "status",
            sa.SmallInteger(),
            server_default=sa.text("1"),
            nullable=False,
            comment="1 启用 / 0 禁用",
        ),
        sa.Column("last_login_at", sa.DateTime(), nullable=True, comment="最近登录"),
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
        sa.UniqueConstraint("username", name="uk_username"),
    )
    op.create_table(
        "sys_config",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("config_key", sa.String(length=64), nullable=False, comment="配置键"),
        sa.Column("config_value", sa.Text(), nullable=False, comment="配置值(JSON 兼容)"),
        sa.Column("remark", sa.String(length=255), nullable=True, comment="说明"),
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
        sa.UniqueConstraint("config_key", name="uk_config_key"),
    )


def downgrade() -> None:
    op.drop_table("sys_config")
    op.drop_table("admin_user")
