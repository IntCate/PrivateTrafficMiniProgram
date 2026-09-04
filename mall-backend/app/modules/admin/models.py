"""后台管理模块 ORM 模型：管理员、系统配置。对齐 docs/database-design.md §3.15/§3.17。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, BaseFields

# 管理员角色（对齐 auth.md §2.2 权限矩阵）
ADMIN_ROLE_ADMIN = "admin"
ADMIN_ROLE_OPERATOR = "operator"
ADMIN_ROLE_FINANCE = "finance"


class AdminUser(Base, BaseFields):
    """后台管理员。"""

    __tablename__ = "admin_user"

    username: Mapped[str] = mapped_column(String(32), unique=True, comment="登录名")
    password: Mapped[str] = mapped_column(String(128), comment="BCrypt 哈希")
    nickname: Mapped[str | None] = mapped_column(String(32), comment="姓名")
    role: Mapped[str] = mapped_column(
        String(20), default=ADMIN_ROLE_ADMIN, comment="admin/operator/finance"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, default=1, comment="1 启用 / 0 禁用"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, comment="最近登录")


class SysConfig(Base, BaseFields):
    """系统配置。"""

    __tablename__ = "sys_config"

    config_key: Mapped[str] = mapped_column(String(64), unique=True, comment="配置键")
    config_value: Mapped[str] = mapped_column(Text, comment="配置值(JSON 兼容)")
    remark: Mapped[str | None] = mapped_column(String(255), comment="说明")
