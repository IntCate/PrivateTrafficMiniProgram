"""add category product sku banner tables

Revision ID: 55fed9b222ea
Revises: 1df292a72279
Create Date: 2026-09-02 09:40:35.124824
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = '55fed9b222ea'
down_revision = '1df292a72279'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'category',
        sa.Column('parent_id', sa.BigInteger(), nullable=False, comment='父分类 ID，0 为顶级'),
        sa.Column('name', sa.String(length=64), nullable=False, comment='分类名'),
        sa.Column('icon', sa.String(length=512), nullable=True, comment='分类图标'),
        sa.Column('sort', sa.Integer(), nullable=False, comment='排序，越小越靠前'),
        sa.Column('status', sa.Integer(), nullable=False, comment='1 启用 / 0 停用'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column('deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_parent_sort', 'parent_id', 'sort'),
    )
    op.create_table(
        'product',
        sa.Column('product_no', sa.String(length=32), nullable=False, comment='商品编号'),
        sa.Column('category_id', sa.BigInteger(), nullable=False, comment='所属分类'),
        sa.Column('brand', sa.String(length=64), nullable=True, comment='品牌'),
        sa.Column('name', sa.String(length=128), nullable=False, comment='商品名称'),
        sa.Column('sub_title', sa.String(length=255), nullable=True, comment='副标题/卖点'),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, comment='销售价'),
        sa.Column('original_price', sa.Numeric(10, 2), nullable=True, comment='划线价/原价'),
        sa.Column('main_image', sa.String(length=512), nullable=False, comment='主图'),
        sa.Column('images', sa.JSON(), nullable=True, comment='图片列表(JSON)'),
        sa.Column('detail_html', sa.Text(), nullable=True, comment='详情富文本'),
        sa.Column('spec', sa.JSON(), nullable=True, comment='参数规格(JSON)'),
        sa.Column('sales', sa.Integer(), nullable=False, comment='已售数量'),
        sa.Column('stock', sa.Integer(), nullable=False, comment='总库存'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签(JSON)'),
        sa.Column('shipping_from', sa.String(length=32), nullable=True, comment='发货地'),
        sa.Column(
            'is_free_shipping', sa.Boolean(), nullable=False, comment='1 包邮 / 0 不包邮'
        ),
        sa.Column('status', sa.Integer(), nullable=False, comment='1 上架 / 0 下架'),
        sa.Column('views', sa.Integer(), nullable=False, comment='浏览量'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column('deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['category.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_no'),
        sa.Index('idx_category_status', 'category_id', 'status'),
        sa.Index('idx_status_sales', 'status', 'sales'),
    )
    op.create_table(
        'product_sku',
        sa.Column('product_id', sa.BigInteger(), nullable=False, comment='商品 ID'),
        sa.Column('sku_code', sa.String(length=64), nullable=False, comment='SKU 编码'),
        sa.Column('attrs', sa.JSON(), nullable=False, comment='属性组(JSON)'),
        sa.Column('sku_text', sa.String(length=128), nullable=False, comment='展示文案'),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, comment='SKU 售价'),
        sa.Column('stock', sa.Integer(), nullable=False, comment='库存'),
        sa.Column('lock_stock', sa.Integer(), nullable=False, comment='锁定库存'),
        sa.Column('image', sa.String(length=512), nullable=True, comment='SKU 专属图'),
        sa.Column('status', sa.Integer(), nullable=False, comment='1 可售 / 0 停售'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column('deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku_code'),
        sa.Index('idx_product', 'product_id'),
    )
    op.create_table(
        'banner',
        sa.Column('position', sa.String(length=20), nullable=False, comment='hero / theme'),
        sa.Column('title', sa.String(length=64), nullable=False, comment='标题'),
        sa.Column('sub_title', sa.String(length=64), nullable=True, comment='副标题/描述'),
        sa.Column('image', sa.String(length=512), nullable=False, comment='图片'),
        sa.Column(
            'link_type', sa.String(length=20), nullable=False,
            comment='none/product/category/page',
        ),
        sa.Column('link_value', sa.String(length=255), nullable=True, comment='跳转目标'),
        sa.Column('sort', sa.Integer(), nullable=False, comment='排序'),
        sa.Column('status', sa.Integer(), nullable=False, comment='1 展示 / 0 隐藏'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column('deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_position_status', 'position', 'status', 'sort'),
    )


def downgrade() -> None:
    op.drop_table('banner')
    op.drop_table('product_sku')
    op.drop_table('product')
    op.drop_table('category')
