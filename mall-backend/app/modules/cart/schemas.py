"""购物车模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from pydantic import Field

from app.common.schemas import CamelModel, CamelRequest


class CartItemOut(CamelModel):
    """购物车项对外信息（对齐 api-design §7.1）。"""

    id: int
    product_id: int
    sku_id: int
    name: str
    sku_text: str
    price: float
    quantity: int
    image: str | None = None
    selected: bool
    stock: int
    on_sale: bool


class CartStateOut(CamelModel):
    """购物车状态（列表 + 合计）。所有购物车接口统一返回该结构。

    内部字段名 items 避免遮蔽内建 list（Pydantic 注解求值问题），
    对外序列化仍输出契约键名 list（serialization_alias）。
    """

    items: list[CartItemOut] = Field(default_factory=list, serialization_alias="list")
    total_price: float = 0.0
    total_quantity: int = 0


class AddItemRequest(CamelRequest):
    """加入购物车（对齐 api-design §7.2）。"""

    sku_id: int
    quantity: int = 1
    selected: bool = False


class UpdateItemRequest(CamelRequest):
    """修改购物车项：三个字段均可选（对齐 api-design §7.3）。"""

    quantity: int | None = None
    selected: bool | None = None
    sku_id: int | None = None


class DeleteItemsRequest(CamelRequest):
    """批量删除（对齐 api-design §7.5）。"""

    ids: list[int]


class SelectAllRequest(CamelRequest):
    """全选/取消全选（对齐 api-design §7.6）。"""

    selected: bool
