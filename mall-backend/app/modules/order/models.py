"""订单模块 ORM 模型：订单、订单明细。对齐 docs/database-design.md §3.7/§3.8。

订单含软删除列（CommonFields，schema.sql §3.7 有 deleted）；
订单明细为纯快照表（无 deleted/updated_at，对齐 schema.sql §3.8）。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, CommonFields

# 订单状态机（对齐 api-design §9 / mock store.js）
ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_PAID = "paid"
ORDER_STATUS_SHIPPED = "shipped"
ORDER_STATUS_COMPLETED = "completed"
ORDER_STATUS_REFUND = "refund"
ORDER_STATUS_CANCELLED = "cancelled"

# 状态文案（对齐 api-design §9.3 / mock store.js STATUS_TEXT）
STATUS_TEXT: dict[str, str] = {
    ORDER_STATUS_PENDING: "待付款",
    ORDER_STATUS_PAID: "待发货",
    ORDER_STATUS_SHIPPED: "待收货",
    ORDER_STATUS_COMPLETED: "已完成",
    ORDER_STATUS_REFUND: "售后中",
    ORDER_STATUS_CANCELLED: "已取消",
}

# 详情页状态描述（对齐 api-design §9.4 / mock store.js STATUS_DESC）
STATUS_DESC: dict[str, str] = {
    ORDER_STATUS_PENDING: "订单已提交，请尽快完成支付",
    ORDER_STATUS_PAID: "商家正在打包，请耐心等待发货",
    ORDER_STATUS_SHIPPED: "商品已发货，请注意查收",
    ORDER_STATUS_COMPLETED: "交易已完成，感谢您的信任",
    ORDER_STATUS_REFUND: "售后处理中，请耐心等待",
    ORDER_STATUS_CANCELLED: "订单已取消，期待再次光临",
}

# 可申请售后的状态集合（对齐 api-design §9.7 / test-cases B5-14）
REFUNDABLE_STATUSES = {ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED, ORDER_STATUS_COMPLETED}

# 角标统计状态（对齐 api-design §9.11 / test-cases B5-5）
STATS_STATUSES = (
    ORDER_STATUS_PENDING,
    ORDER_STATUS_PAID,
    ORDER_STATUS_SHIPPED,
    ORDER_STATUS_REFUND,
)


class Order(Base, CommonFields):
    """订单主表。"""

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_no", name="uk_order_no"),
        Index("idx_user_status", "user_id", "status", "created_at"),
        Index("idx_status", "status", "created_at"),
    )

    order_no: Mapped[str] = mapped_column(String(32), comment="订单号 K+时间戳+3位随机")
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("member.id"), comment="会员 ID"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=ORDER_STATUS_PENDING,
        comment="pending/paid/shipped/completed/refund/cancelled",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="商品总金额"
    )
    freight: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="运费"
    )
    pay_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="实付金额"
    )
    coupon_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="优惠券抵扣"
    )
    points_used: Mapped[int] = mapped_column(Integer, default=0, comment="积分抵扣")
    receiver_name: Mapped[str] = mapped_column(String(32), comment="收货人快照")
    receiver_phone: Mapped[str] = mapped_column(String(20), comment="收货电话快照")
    receiver_region: Mapped[str] = mapped_column(String(128), comment="省市区快照")
    receiver_detail: Mapped[str] = mapped_column(String(255), comment="详细地址快照")
    pay_type: Mapped[str | None] = mapped_column(String(20), comment="wechat/mock")
    transaction_id: Mapped[str | None] = mapped_column(String(64), comment="微信支付单号")
    remark: Mapped[str | None] = mapped_column(String(255), comment="买家备注")
    cancel_reason: Mapped[str | None] = mapped_column(String(255), comment="取消/关闭原因")
    refund_reason: Mapped[str | None] = mapped_column(String(255), comment="售后/退款原因")
    refund_type: Mapped[str | None] = mapped_column(
        String(20), comment="refund 仅退款 / return 退货退款"
    )
    refund_time: Mapped[datetime | None] = mapped_column(DateTime, comment="申请售后时间")
    pay_time: Mapped[datetime | None] = mapped_column(DateTime, comment="支付时间")
    ship_time: Mapped[datetime | None] = mapped_column(DateTime, comment="发货时间")
    finish_time: Mapped[datetime | None] = mapped_column(DateTime, comment="完成时间")


class OrderItem(Base):
    """订单明细（快照，无软删除/更新时间列）。"""

    __tablename__ = "order_item"
    __table_args__ = (
        Index("idx_order", "order_id"),
        Index("idx_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id"), comment="订单 ID"
    )
    product_id: Mapped[int] = mapped_column(BigInteger, comment="商品 ID")
    sku_id: Mapped[int] = mapped_column(BigInteger, comment="SKU ID")
    product_name: Mapped[str] = mapped_column(String(128), comment="商品名快照")
    sku_text: Mapped[str] = mapped_column(String(128), comment="SKU 文案快照")
    image: Mapped[str] = mapped_column(String(512), comment="主图快照")
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), comment="成交单价快照"
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, comment="数量")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
