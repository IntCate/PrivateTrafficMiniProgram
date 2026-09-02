"""通用工具：订单号、随机数、时间、脱敏。"""
from __future__ import annotations

import random
import re
from datetime import datetime

_PHONE_RE = re.compile(r"(\d{3})\d{4}(\d{4})")
_OPENID_RE = re.compile(r"^(.{6}).*(.{4})$")


def generate_order_no() -> str:
    """订单号：K + yyyyMMddHHmmss + 3 位随机。"""
    return f"K{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(0, 999):03d}"


def mask_phone(phone: str) -> str:
    """手机号脱敏：138****1234。"""
    return _PHONE_RE.sub(r"\1****\2", phone)


def mask_token(token: str) -> str:
    """token/JWT 脱敏：前 8 后 4。"""
    if len(token) <= 12:
        return "****"
    return f"{token[:8]}****{token[-4:]}"


def mask_openid(openid: str) -> str:
    """openid 脱敏：前 6 后 4。"""
    m = _OPENID_RE.match(openid)
    if not m:
        return "****"
    return f"{m.group(1)}****{m.group(2)}"


def mask_address_detail(detail: str) -> str:
    """详细地址打码：保留前 2 字符，其余替换为 *。"""
    if len(detail) <= 2:
        return "****"
    return detail[:2] + "*" * (len(detail) - 2)
