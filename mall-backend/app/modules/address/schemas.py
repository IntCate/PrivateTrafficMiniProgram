"""收货地址模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from app.common.schemas import CamelModel, CamelRequest


class AddressOut(CamelModel):
    """地址对外信息（对齐 api-design §8.1）。"""

    id: int
    name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    is_default: bool
    region_text: str


class AddressRequest(CamelRequest):
    """新增/编辑地址请求（对齐 api-design §8.2/8.3，全字段必传整体覆盖）。"""

    name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    is_default: bool = False
