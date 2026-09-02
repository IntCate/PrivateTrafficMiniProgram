"""会员中心模块路由。对齐 docs/api-design.md §11。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps import get_current_member
from app.core.database import get_db
from app.core.response import ok
from app.modules.auth.models import Member
from app.modules.member.schemas import UpdateProfileRequest
from app.modules.member.service import get_overview, update_profile

router = APIRouter(prefix="/member", tags=["member"])


@router.get("/overview")
def member_overview_endpoint(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """我的页聚合数据 🔒（对齐 api-design §11.1）。"""
    return ok(get_overview(db, member))


@router.put("/profile")
def member_profile_endpoint(
    req: UpdateProfileRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
) -> dict:
    """更新本人昵称/头像 🔒（对齐 api-design §11.2）。"""
    return ok(update_profile(db, member, req))
