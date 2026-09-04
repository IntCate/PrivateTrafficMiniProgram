"""认证模块 ORM 模型：会员、会员会话。对齐 docs/database-design.md §3.1/§3.16。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, BaseFields, SoftDeleteMixin

# 会员等级字典（对应接口 memberLevel，新会员默认 bronze）
MEMBER_LEVEL_DEFAULT = "bronze"


class Member(Base, BaseFields, SoftDeleteMixin):
    """会员。"""

    __tablename__ = "member"

    openid: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, comment="微信 openid"
    )
    unionid: Mapped[str | None] = mapped_column(String(64), comment="微信 unionid（多端绑定预留）")
    nickname: Mapped[str | None] = mapped_column(String(64), comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(512), comment="头像 URL")
    phone: Mapped[str | None] = mapped_column(String(20), index=True, comment="手机号")
    gender: Mapped[int] = mapped_column(default=0, comment="0 未知 / 1 男 / 2 女")
    member_level: Mapped[str] = mapped_column(
        String(20), default=MEMBER_LEVEL_DEFAULT, comment="会员等级 bronze/silver/gold/platinum"
    )
    points: Mapped[int] = mapped_column(Integer, default=0, comment="当前积分")
    status: Mapped[int] = mapped_column(default=1, comment="状态：1 正常 0 禁用")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, comment="最近登录时间")


class MemberSession(Base, BaseFields, SoftDeleteMixin):
    """会员会话（C 端 token）。"""

    __tablename__ = "member_session"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("member.id"), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="不透明 token")
    expires_at: Mapped[datetime] = mapped_column(DateTime, comment="过期时间")
