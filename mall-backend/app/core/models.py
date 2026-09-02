"""模型基类：Base、CommonFields（id/created_at/updated_at/deleted 逻辑删除）。"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类。"""


class CommonFields:
    """通用字段混入：主键、时间戳、逻辑删除标记。"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="逻辑删除标记")
