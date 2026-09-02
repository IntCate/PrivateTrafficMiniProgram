"""Pydantic 基类：API 字段统一驼峰、DB 字段下划线自动转换。

对齐 docs/api-design.md §1.5：请求/响应字段使用驼峰，DB 字段为下划线。
业务 schema 继承本基类，用下划线声明字段名，序列化出参时自动转驼峰。
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """驼峰输出基类：字段以下划线声明，对外序列化为驼峰。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class CamelRequest(BaseModel):
    """驼峰输入基类：接收驼峰请求体，声明字段转回下划线。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
