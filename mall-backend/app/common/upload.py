"""上传抽象：本地磁盘存储，OSS 预留接口。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


class UploadError(Exception):
    pass


async def save_upload(file: UploadFile, subdir: str = "") -> str:
    """保存上传文件到本地磁盘，返回相对路径。"""
    ext = Path(file.filename or "").suffix or ""
    filename = f"{uuid.uuid4().hex}{ext}"
    target_dir = Path(settings.upload_dir) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    content = await file.read()
    target.write_bytes(content)
    return f"{subdir}/{filename}" if subdir else filename
