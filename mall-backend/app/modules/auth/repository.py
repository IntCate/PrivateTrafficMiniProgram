"""认证模块数据访问。"""
from __future__ import annotations

from app.common.repository import BaseRepository
from app.modules.auth.models import Member, MemberSession


class MemberRepository(BaseRepository[Member]):
    model = Member


class MemberSessionRepository(BaseRepository[MemberSession]):
    model = MemberSession
