"""收藏模块数据访问。"""
from __future__ import annotations

from typing import Any, cast

from sqlalchemy import delete, func, select
from sqlalchemy.engine import CursorResult

from app.common.repository import BaseRepository
from app.modules.favorite.models import Favorite


class FavoriteRepository(BaseRepository[Favorite]):
    model = Favorite

    def list_by_user(
        self, user_id: int, page: int, page_size: int
    ) -> tuple[list[Favorite], int]:
        """按用户分页查询收藏（新收藏在前）。"""
        count_stmt = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        total = self.db.scalar(count_stmt) or 0
        rows = list(
            self.db.scalars(
                select(Favorite)
                .where(Favorite.user_id == user_id)
                .order_by(Favorite.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return rows, total

    def get_by_user_product(self, user_id: int, product_id: int) -> Favorite | None:
        """按 user + product 查询（幂等去重）。"""
        stmt = select(Favorite).where(
            Favorite.user_id == user_id, Favorite.product_id == product_id
        )
        return self.db.scalar(stmt)

    def remove_by_product(self, user_id: int, product_id: int) -> int:
        """按 user + product 删除，返回删除行数（幂等）。"""
        stmt = delete(Favorite).where(
            Favorite.user_id == user_id, Favorite.product_id == product_id
        )
        result = cast(CursorResult[Any], self.db.execute(stmt))
        return result.rowcount or 0
