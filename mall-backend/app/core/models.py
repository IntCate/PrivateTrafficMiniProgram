"""模型基类：Base、BaseFields（主键/时间戳）、SoftDeleteMixin（逻辑删除）。

- BaseFields：id / created_at / updated_at，几乎所有业务表都需要；
- SoftDeleteMixin：deleted 逻辑删除列，仅真正需要软删的模型显式继承。

此前 CommonFields 会把 deleted 无条件注入所有继承模型，导致 member/product 这类
已用 status 做软开关的表也冗余带 deleted。拆分后按需显式选择。
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类。"""


class BaseFields:
    """基础字段混入：主键、创建/更新时间戳。"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class SoftDeleteMixin:
    """逻辑删除混入：仅真正需要软删的模型显式继承。"""

    deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="逻辑删除标记")