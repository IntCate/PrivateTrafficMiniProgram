"""通用工具单元测试。"""
from __future__ import annotations

from app.common.utils import generate_order_no, mask_phone, mask_token


def test_generate_order_no() -> None:
    no = generate_order_no()
    assert no.startswith("K")
    assert len(no) == 1 + 14 + 3


def test_mask_phone() -> None:
    assert mask_phone("13812341234") == "138****1234"


def test_mask_token() -> None:
    assert mask_token("abcdefghijklmnop") == "abcdefgh****mnop"
