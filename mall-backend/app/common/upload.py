"""上传抽象：本地磁盘存储，OSS 预留接口。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


class UploadError(Exception):
    pass


def save_bytes(content: bytes, ext: str = "", subdir: str = "") -> str:
    """保存字节流到本地磁盘（uploads/<subdir>/），返回相对路径（不含 /uploads 前缀）。"""
    filename = f"{uuid.uuid4().hex}{ext}"
    target_dir = Path(settings.upload_dir) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_bytes(content)
    return f"{subdir}/{filename}" if subdir else filename


async def save_upload(file: UploadFile, subdir: str = "") -> str:
    """解析 UploadFile 后复用 save_bytes 落盘，返回相对路径。"""
    ext = Path(file.filename or "").suffix or ""
    content = await file.read()
    return save_bytes(content, ext, subdir)
