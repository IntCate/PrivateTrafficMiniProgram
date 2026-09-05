"""通用文件上传路由。对齐 docs/api-design §12 售后凭证图与 §11 头像上传。"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from app.common.deps import get_current_member
from app.common.upload import save_bytes
from app.core.response import ok
from app.modules.auth.models import Member

router = APIRouter(tags=["common"])

# 允许的图片类型与体积上限（5MB）
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_SIZE = 5 * 1024 * 1024

# 上传用途 → 存储子目录（对齐 api-design §12.3 / §11.2）
ALLOWED_CATEGORIES = {
    "after_sale": "after_sale",
    "avatar": "avatar",
}


class UploadOut(BaseModel):
    url: str


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    member: Member = Depends(get_current_member),
    category: str = Form("after_sale"),
) -> dict:
    """图片上传 🔒（对齐 api-design §9.8 图片字段）。返回可访问的相对 URL。"""
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail="不支持的图片用途")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 jpg/jpeg/png/gif/webp 图片")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    relative = save_bytes(content, suffix, category)
    return ok(UploadOut(url=f"/uploads/{relative}").model_dump())