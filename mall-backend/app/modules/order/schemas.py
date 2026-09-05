"""订单模块 Pydantic 出入参。字段下划线声明，对外序列化驼峰。"""
from __future__ import annotations

from pydantic import Field

from app.common.schemas import CamelModel, CamelRequest


class PreviewItemOut(CamelModel):
    """结算预览商品项（对齐 api-design §9.1）。"""

    cart_item_id: int
    product_id: int
    sku_id: int
    name: str
    sku_text: str
    price: float
    quantity: int
    image: str | None = None
    stock: int


class PreviewAddressOut(CamelModel):
    """结算预览地址项（对齐 api-design §9.1）。"""

    id: int
    name: str
    phone: str
    region_text: str
    detail: str
    is_default: bool


class PreviewOut(CamelModel):
    """结算预览（对齐 api-design §9.1）。"""

    items: list[PreviewItemOut]
    total_amount: float
    freight: float
    coupon_amount: float = 0.0
    points_amount: float = 0.0
    pay_amount: float
    addresses: list[PreviewAddressOut]


class UnavailableItem(CamelModel):
    """不可售项（1203 携带，对齐 api-design §9.1）。"""

    cart_item_id: int
    product_id: int
    sku_id: int
    name: str
    sku_text: str


class ReceiverOut(CamelModel):
    """收货人快照（对齐 api-design §9.2/§9.4）。"""

    name: str
    phone: str
    region_text: str
    detail: str


class OrderItemOut(CamelModel):
    """订单明细（对齐 api-design §9.2）。"""

    id: int
    product_name: str
    sku_text: str
    price: float
    quantity: int
    image: str | None = None


class OrderListItemOut(CamelModel):
    """订单列表项（对齐 api-design §9.3）。"""

    id: int
    order_no: str
    status: str
    status_text: str
    total_amount: float
    freight: float
    coupon_amount: float = 0.0
    points_used: int = 0
    pay_amount: float
    receiver: ReceiverOut
    items: list[OrderItemOut]
    create_time: str
    pay_deadline: str | None = None
    available_actions: list[str]


class OrderDetailOut(OrderListItemOut):
    """订单详情（对齐 api-design §9.4，在列表项基础上附加详情字段）。"""

    status_desc: str
    pay_type: str | None = None
    pay_time: str | None = None
    ship_time: str | None = None
    finish_time: str | None = None


class OrderListOut(CamelModel):
    """订单分页列表（对齐 api-design §9.3）。

    内部字段名 items 避免遮蔽内建 list，对外序列化输出契约键名 list。
    """

    items: list[OrderListItemOut] = Field(default_factory=list, serialization_alias="list")
    total: int
    page: int
    pageSize: int
    hasMore: bool


class OrderStatsOut(CamelModel):
    """订单状态角标（对齐 api-design §9.11）。"""

    pending: int = 0
    paid: int = 0
    shipped: int = 0
    refund: int = 0


class CreateOrderItemRequest(CamelRequest):
    """创建订单明细项（对齐 api-design §9.2）。"""

    sku_id: int
    quantity: int


class CreateOrderRequest(CamelRequest):
    """创建订单（对齐 api-design §9.2）。"""

    address_id: int
    items: list[CreateOrderItemRequest]
    user_coupon_id: int | None = None
    points_used: int = 0


class CreateDirectOrderRequest(CamelRequest):
    """直购下单（对齐 api-design §9.1 直购口径）。"""

    address_id: int
    sku_id: int
    quantity: int


class PayOrderRequest(CamelRequest):
    """支付订单（对齐 api-design §9.5）。"""

    pay_type: str = "mock"


class CancelOrderRequest(CamelRequest):
    """取消订单（对齐 api-design §9.6）。"""

    reason: str | None = None


class RefundOrderRequest(CamelRequest):
    """申请售后/退款（对齐 api-design §9.7）。"""

    reason: str | None = None
    type: str | None = None
