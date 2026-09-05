"""通用文件上传路由。对齐 docs/api-design §12 售后凭证图与 §11 头像上传。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from app.common.deps import get_current_member
from app.core.config import settings
from app.core.response import ok
from app.modules.auth.models import Member

router = APIRouter(tags=["common"])

# 允许的图片类型与体积上限（5MB）
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_SIZE = 5 * 1024 * 1024


class UploadOut(BaseModel):
    url: str


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    member: Member = Depends(get_current_member),
) -> dict:
    """图片上传 🔒（对齐 api-design §9.8 图片字段）。返回可访问的相对 URL。"""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 jpg/jpeg/png/gif/webp 图片")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    relative = _save_bytes(content, suffix)
    return ok(UploadOut(url=f"/uploads/{relative}").model_dump())


def _save_bytes(content: bytes, suffix: str) -> str:
    """写入本地磁盘 uploads/after_sale/，返回相对路径。"""
    target_dir = Path(settings.upload_dir) / "after_sale"
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    (target_dir / filename).write_bytes(content)
    return f"after_sale/{filename}"