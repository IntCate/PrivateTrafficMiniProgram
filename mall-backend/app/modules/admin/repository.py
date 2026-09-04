"""后台管理模块数据访问。"""
from __future__ import annotations

from sqlalchemy import func, select

from app.common.repository import BaseRepository
from app.modules.admin.models import AdminUser, SysConfig


class AdminUserRepository(BaseRepository[AdminUser]):
    model = AdminUser

    def get_by_username(self, username: str) -> AdminUser | None:
        return self.get_by(username=username)

    def page_admins(self, page: int, page_size: int) -> tuple[list[AdminUser], int]:
        stmt = select(AdminUser).order_by(AdminUser.id.asc())
        count_stmt = select(func.count(AdminUser.id))
        total = self.db.scalar(count_stmt) or 0
        rows = list(
            self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size))
        )
        return rows, total


class SysConfigRepository(BaseRepository[SysConfig]):
    model = SysConfig

    def get_by_key(self, key: str) -> SysConfig | None:
        return self.get_by(config_key=key)

    def list_all(self) -> list[SysConfig]:
        stmt = select(SysConfig).order_by(SysConfig.id.asc())
        return list(self.db.scalars(stmt))
