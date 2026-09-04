# 快乐购商城 - 数据库设计文档

> 项目：快乐购（自营私域商城小程序）
> 版本：v1.0（首个后端版本）
> 数据库：MySQL 8.x（首版不引入 Redis）
> 字符集：utf8mb4 / utf8mb4_unicode_ci

---

## 1. 设计概览

### 1.1 设计依据

本文档依据 `mall-miniapp-uni` 前端已完成的 12 个页面及其本地数据层（`src/api/mock/store.js`）推导而来。前端当前使用本地 mock 数据层（经 `src/api/request.js` 的 `mockRequest` 分流，`src/api/config.js` 的 `useMock` 一键切换真实后端），实体与字段均与前端现有数据结构对齐，保证后端接替后前端改动最小。

### 1.2 覆盖的模块

| 模块 | 页面/功能 | 备注 |
| --- | --- | --- |
| 用户/会员 | 我的页、首页问候区、设置页 | 含会员等级、积分、优惠券 |
| 商品 | 商品列表、商品详情 | 分类、SKU、搜索、详情参数 |
| 购物车 | 购物车页 | 勾选、数量、删除、批量管理 |
| 订单 | 确认订单、订单列表、订单详情 | 下单、支付、取消、收货、售后 |
| 收货地址 | 地址列表、地址编辑 | 默认地址 |
| 收藏 | 我的收藏 | — |
| 运营 | 首页横幅、主题精选 | — |
| 管理后台 | 预留 | 商品/订单/会员/运营位管理 |

### 1.3 命名约定

- 表名：小写下划线，业务名词复数（`orders` 避让 `order` 关键字）
- 字段名：小写下划线
- 主键：`id BIGINT UNSIGNED AUTO_INCREMENT`
- 通用字段：`created_at` / `updated_at`（DATETIME）
- 金额：一律 `DECIMAL(10,2)`，单位元
- 状态字段：使用字符串状态码（与前端现有 `pending/paid/shipped/completed/refund` 保持一致），便于联调与可读性；入库前 `CHECK` 或由应用层校验
- 删除策略：拆分为 `BaseFields`（id/created_at/updated_at 通用字段）与可选 `SoftDeleteMixin`（deleted 逻辑删除），由模型按需显式继承。启用 `deleted` 软删的业务表为 `member`/`member_session`/`product`/`product_sku`/`orders`/`shipping_address`（6 张，与 ORM/迁移/schema.sql 三端一致）；`category`/`banner` 仅以 `status` 软开关、不启用 `deleted`；`order_item`/`cart`/`favorite` 为关系/快照表亦不启用。商品、会员以状态字段软开关 + `deleted` 软删双层兜底，不物理删除

### 1.4 约定说明

- 所有金额计算（订单合计、退款等）最终以应用层计算的 `DECIMAL` 为准，避免浮点误差
- `region`（省市区）拆分为 `province` / `city` / `district` 三个字段，便于索引与统计；同时保留快照语义
- 订单/订单项中商品名称、SKU 文案、价格、图片均做**冗余快照**，防止商品改价或下架后订单展示失真
- 时间统一存储 MySQL `DATETIME`，接口层输出 `yyyy-MM-dd HH:mm:ss`

---

## 2. ER 关系总览

```text
member (会员)
  ├──< user_coupon （会员 1 — N 优惠券领取记录）
  ├──< favorite    （会员 1 — N 收藏）
  ├──< cart        （会员 1 — N 购物车项）
  ├──< shipping_address （会员 1 — N 收货地址）
  ├──< orders      （会员 1 — N 订单）
  │     └──< order_item （订单 1 — N 明细）
  │     └──< after_sale （订单 1 — N 售后单）
  └──< points_log  （会员 1 — N 积分明细）

category (分类)
  └──< product （分类 1 — N 商品）
        └──< product_sku （商品 1 — N SKU）

coupon (券模板)
  └──< user_coupon（模板 1 — N 发放记录）
```

---

## 3. 数据表详细设计

### 3.1 会员表 `member`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| openid | VARCHAR(64) | NO | — | 微信小程序 openid，唯一索引 |
| unionid | VARCHAR(64) | YES | NULL | 微信 unionid（多端绑定预留） |
| nickname | VARCHAR(64) | YES | NULL | 昵称 |
| avatar | VARCHAR(512) | YES | NULL | 头像 URL |
| phone | VARCHAR(20) | YES | NULL | 手机号（脱敏展示由应用层处理） |
| gender | TINYINT | YES | 0 | 0 未知 / 1 男 / 2 女 |
| member_level | VARCHAR(20) | NO | 'bronze' | 会员等级：bronze/silver/gold/platinum（新会员默认 bronze，见下方等级字典） |
| points | INT UNSIGNED | NO | 0 | 当前积分（由积分流水累计，新会员默认 0，见 3.12） |
| status | TINYINT | NO | 1 | 1 正常 / 0 禁用 |
| last_login_at | DATETIME | YES | NULL | 最近登录时间 |
| created_at | DATETIME | NO | 当前时间 | 注册时间 |
| updated_at | DATETIME | NO | 当前时间 | 更新时间 |

等级字典：`bronze`=普通 / `silver`=白银 / `gold`=黄金 / `platinum`=铂金（与 PRD §4.1 默认等级、接口 `memberLevelText` 展示一致）

索引：
- `uk_openid`（openid）
- `idx_phone`（phone）

### 3.2 商品分类表 `category`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| parent_id | BIGINT UNSIGNED | NO | 0 | 父分类 ID，0 为顶级（预留二级分类） |
| name | VARCHAR(64) | NO | — | 分类名（前端：鞋服/箱包/数码/美妆/家居） |
| icon | VARCHAR(512) | YES | NULL | 分类图标 |
| sort | INT | NO | 0 | 排序，越小越靠前 |
| status | TINYINT | NO | 1 | 1 启用 / 0 停用 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：`idx_parent_sort`（parent_id, sort）

> 前端首页/商品页固定分类：`['全部', '鞋服', '箱包', '数码', '美妆', '家居']`，需在初始化数据脚本（SQL）中预置。

### 3.3 商品表 `product`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键（前端用 `sneaker-1` 等字符串 ID，后端换为大整型并保留对外编号 `product_no`） |
| product_no | VARCHAR(32) | NO | — | 商品编号（对外展示/追踪），唯一索引 |
| category_id | BIGINT UNSIGNED | NO | — | 所属分类，外键 category(id) |
| brand | VARCHAR(64) | YES | NULL | 品牌（预留） |
| name | VARCHAR(128) | NO | — | 商品名称 |
| sub_title | VARCHAR(255) | YES | NULL | 副标题/卖点描述（前端 `desc`） |
| price | DECIMAL(10,2) | NO | 0 | 销售价 |
| original_price | DECIMAL(10,2) | YES | NULL | 划线价/原价 |
| main_image | VARCHAR(512) | NO | — | 主图 |
| images | JSON | YES | NULL | 图片列表（`["...","..."]`），商品详情轮播 |
| detail_html | TEXT | YES | NULL | 商品详情富文本（详情 tab） |
| spec | JSON | YES | NULL | 参数规格（如 `{"材质":"织物+TPU"}`，参数规格 tab） |
| sales | INT UNSIGNED | NO | 0 | 已售数量（前端展示"已售 1.2万+"） |
| stock | INT UNSIGNED | NO | 0 | 总库存（兜底，精确库存以 SKU 为准） |
| tags | JSON | YES | NULL | 标签（如 `["热销","包邮"]`） |
| shipping_from | VARCHAR(32) | YES | NULL | 发货地（前端"上海发货"） |
| is_free_shipping | TINYINT | NO | 1 | 是否包邮 1/0 |
| status | TINYINT | NO | 1 | 1 上架 / 0 下架 |
| views | INT UNSIGNED | NO | 0 | 浏览量 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：
- `uk_product_no`（product_no）
- `idx_category_status`（category_id, status, sort）
- `idx_status_sales`（status, sales）

> 前端 `productCatalog` 10 条示例商品作为初始化数据预置。

### 3.4 SKU 表 `product_sku`

对应前端商品详情弹层的属性选择（如 `云雾白；40`），SKU 文案统一由各属性值拼接（`；` 分隔）。属性维度不固定，支持任意数量属性组（如"颜色 × 尺码 × 款式"）。

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| product_id | BIGINT UNSIGNED | NO | — | 外键 product(id) |
| sku_code | VARCHAR(64) | NO | — | SKU 编码，唯一索引 |
| attrs | JSON | NO | — | 通用属性组数组 `[{name, value}, ...]`，如 `[{"name":"颜色","value":"云雾白"},{"name":"尺码","value":"40"}]` |
| sku_text | VARCHAR(128) | NO | — | 展示文案，如 `云雾白；40` |
| price | DECIMAL(10,2) | NO | 0 | SKU 售价（可覆盖商品价） |
| stock | INT UNSIGNED | NO | 0 | 库存 |
| lock_stock | INT UNSIGNED | NO | 0 | 锁定库存（下单减锁，支付扣减或超时回补） |
| image | VARCHAR(512) | YES | NULL | SKU 专属图 |
| status | TINYINT | NO | 1 | 1 可售 / 0 停售 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：
- `uk_sku_code`（sku_code）
- `idx_product`（product_id）

### 3.5 购物车表 `cart`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| user_id | BIGINT UNSIGNED | NO | — | 外键 member(id) |
| product_id | BIGINT UNSIGNED | NO | — | 外键 product(id) |
| sku_id | BIGINT UNSIGNED | NO | — | 外键 product_sku(id) |
| quantity | INT UNSIGNED | NO | 1 | 数量 |
| selected | TINYINT | NO | 0 | 勾选状态 1/0（对应前端 `selected`，结算仅统计选中项）；**加购默认 `0`（不勾选）**，需用户手动勾选后参与结算 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：`uk_user_sku`（user_id, sku_id）唯一；`idx_user`（user_id）

> 说明：购物车归属"已登录用户"，同一用户同一 SKU 幂等（加购合并数量）。首版直接读写 MySQL，不引入缓存。

### 3.6 收货地址表 `shipping_address`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| user_id | BIGINT UNSIGNED | NO | — | 外键 member(id) |
| name | VARCHAR(32) | NO | — | 收货人姓名 |
| phone | VARCHAR(20) | NO | — | 手机号（校验 `^1\d{10}$`） |
| province | VARCHAR(32) | NO | — | 省（前端 region[0]） |
| city | VARCHAR(32) | NO | — | 市（region[1]） |
| district | VARCHAR(32) | NO | — | 区（region[2]） |
| detail | VARCHAR(255) | NO | — | 详细地址 |
| is_default | TINYINT | NO | 0 | 是否默认 1/0（同用户唯一默认由应用层保证） |
| deleted | TINYINT | NO | 0 | 逻辑删除 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：`idx_user_default`（user_id, is_default）；`idx_user_deleted`（user_id, deleted）

### 3.7 订单表 `orders`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| order_no | VARCHAR(32) | NO | — | 订单号（`K+yyyyMMddHHmmss+3位随机`，与 PRD §4.8 一致），唯一索引 |
| user_id | BIGINT UNSIGNED | NO | — | 外键 member(id) |
| status | VARCHAR(20) | NO | 'pending' | pending 待付款 / paid 待发货 / shipped 待收货 / completed 已完成 / refund 售后中 / cancelled 已取消 |
| total_amount | DECIMAL(10,2) | NO | 0 | 商品总金额（快照 sum） |
| freight | DECIMAL(10,2) | NO | 0 | 运费（当前前端固定 0） |
| pay_amount | DECIMAL(10,2) | NO | 0 | 实付金额 |
| coupon_amount | DECIMAL(10,2) | NO | 0 | 优惠券抵扣（预留，当前 0） |
| points_used | INT UNSIGNED | NO | 0 | 积分抵扣（预留） |
| receiver_name | VARCHAR(32) | NO | — | 收货人快照 |
| receiver_phone | VARCHAR(20) | NO | — | 收货电话快照 |
| receiver_region | VARCHAR(128) | NO | — | 省市区快照，如 `上海市 上海市 浦东新区` |
| receiver_detail | VARCHAR(255) | NO | — | 详细地址快照 |
| pay_type | VARCHAR(20) | YES | NULL | 支付方式：wechat / mock（暂未接微信支付） |
| transaction_id | VARCHAR(64) | YES | NULL | 微信支付单号（预留） |
| remark | VARCHAR(255) | YES | NULL | 买家备注 |
| cancel_reason | VARCHAR(255) | YES | NULL | 取消/关闭原因 |
| refund_reason | VARCHAR(255) | YES | NULL | 售后/退款原因 |
| refund_type | VARCHAR(20) | YES | NULL | 退款类型：refund 仅退款 / return 退货退款 |
| refund_time | DATETIME | YES | NULL | 申请售后时间 |
| pay_time | DATETIME | YES | NULL | 支付时间 |
| ship_time | DATETIME | YES | NULL | 发货时间 |
| finish_time | DATETIME | YES | NULL | 完成时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：
- `uk_order_no`（order_no）
- `idx_user_status`（user_id, status, created_at）
- `idx_status`（status, created_at）—— 后台按状态运营使用

> 状态流转：`pending → paid → shipped → completed`；`pending → cancelled`；`paid/shipped/completed → refund`（申请售后/退款，见 api-design §9.7）。

### 3.8 订单明细表 `order_item`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| order_id | BIGINT UNSIGNED | NO | — | 外键 orders(id) |
| product_id | BIGINT UNSIGNED | NO | — | 商品 ID |
| sku_id | BIGINT UNSIGNED | NO | — | SKU ID |
| product_name | VARCHAR(128) | NO | — | 商品名快照 |
| sku_text | VARCHAR(128) | NO | — | SKU 文案快照（如 `云雾白；40`） |
| image | VARCHAR(512) | NO | — | 主图快照 |
| price | DECIMAL(10,2) | NO | 0 | 成交单价快照 |
| quantity | INT UNSIGNED | NO | 0 | 数量 |
| created_at | DATETIME | NO | 当前时间 | — |

索引：`idx_order`（order_id）；`idx_product`（product_id）

### 3.9 收藏表 `favorite`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| user_id | BIGINT UNSIGNED | NO | — | 外键 member(id) |
| product_id | BIGINT UNSIGNED | NO | — | 外键 product(id) |
| created_at | DATETIME | NO | 当前时间 | — |

索引：`uk_user_product`（user_id, product_id）唯一

### 3.10 优惠券模板表 `coupon`

> 前端"我的页/首页优惠券 5 张"为静态展示，本表与 3.11 为功能预留。

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| name | VARCHAR(64) | NO | — | 券名称 |
| type | VARCHAR(20) | NO | 'cash' | cash 满减 / discount 折扣 / shipping 免运费 |
| amount | DECIMAL(10,2) | YES | NULL | 满减金额（cash 用） |
| discount | DECIMAL(4,2) | YES | NULL | 折扣（discount 用，如 0.85） |
| min_amount | DECIMAL(10,2) | NO | 0 | 使用门槛 |
| total_count | INT | NO | 0 | 发放总量，0 不限 |
| received_count | INT | NO | 0 | 已领取数量 |
| valid_start | DATETIME | YES | NULL | 生效时间 |
| valid_end | DATETIME | YES | NULL | 失效时间 |
| status | TINYINT | NO | 1 | 1 启用 / 0 停用 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

### 3.11 用户优惠券表 `user_coupon`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| user_id | BIGINT UNSIGNED | NO | — | 外键 member(id) |
| coupon_id | BIGINT UNSIGNED | NO | — | 外键 coupon(id) |
| status | VARCHAR(20) | NO | 'unused' | unused 未使用 / used 已使用 / expired 已过期 |
| used_order_no | VARCHAR(32) | YES | NULL | 核销订单号 |
| used_at | DATETIME | YES | NULL | 使用时间 |
| created_at | DATETIME | NO | 当前时间 | — |

索引：`idx_user_status`（user_id, status）

### 3.12 积分明细表 `points_log`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| user_id | BIGINT UNSIGNED | NO | — | 外键 member(id) |
| change | INT | NO | 0 | 变动值（正增负减） |
| balance | INT | NO | 0 | 变动后余额 |
| type | VARCHAR(20) | NO | — | earn 获得 / consume 消费 / refund 退回 |
| biz_type | VARCHAR(32) | NO | — | 业务场景：order/promotion/admin |
| remark | VARCHAR(255) | YES | NULL | 说明 |
| created_at | DATETIME | NO | 当前时间 | — |

索引：`idx_user`（user_id, created_at）

### 3.13 运营位表 `banner`

对应首页"主横幅 + 主题精选"（前端 `themes` 轮播 4 张卡片 + hero 横幅）。

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| position | VARCHAR(20) | NO | — | hero 主横幅 / theme 主题精选 |
| title | VARCHAR(64) | NO | — | 标题（如"夏季焕新"） |
| sub_title | VARCHAR(64) | YES | NULL | 副标题/描述（如"轻盈出行"） |
| image | VARCHAR(512) | NO | — | 图片 |
| link_type | VARCHAR(20) | NO | 'none' | none / product / category / page |
| link_value | VARCHAR(255) | YES | NULL | 跳转目标（商品 ID / 分类 ID / 页面路径） |
| sort | INT | NO | 0 | 排序 |
| status | TINYINT | NO | 1 | 1 展示 / 0 隐藏 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：`idx_position_status`（position, status, sort）

### 3.14 售后单表 `after_sale`

> 订单存在 `refund`（售后）状态，前端"售后/退款"tab 已预留，本表为完整售后工单扩展。当前 P0 的 `POST /api/orders/{id}/refund`（api-design §9.7）为轻量级订单级退款，直接在 `orders` 表记录 `refund_reason`/`refund_type`/`refund_time` 并置状态为 `refund`；后续 P1 售后工单（审核/退货物流/退款金额）落本表，与 `orders` 表 1:N 关联。

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| order_id | BIGINT UNSIGNED | NO | — | 外键 orders(id) |
| user_id | BIGINT UNSIGNED | NO | — | 外键 member(id) |
| type | VARCHAR(20) | NO | — | refund 仅退款 / return 退货退款 |
| reason | VARCHAR(255) | NO | — | 申请原因 |
| amount | DECIMAL(10,2) | NO | 0 | 申请金额 |
| status | VARCHAR(20) | NO | 'applying' | applying 申请中 / approved 通过 / rejected 驳回 / refunded 已退款 / closed 关闭 |
| images | JSON | YES | NULL | 凭证图片 |
| audit_remark | VARCHAR(255) | YES | NULL | 审核意见 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：`idx_order`（order_id）；`idx_user`（user_id, status）

### 3.15 管理员表 `admin_user`

> 管理后台（预留）：商品/订单/会员/运营位维护。

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| username | VARCHAR(32) | NO | — | 登录名，唯一 |
| password | VARCHAR(128) | NO | — | BCrypt 哈希（禁止明文/禁用 MD5） |
| nickname | VARCHAR(32) | YES | NULL | 姓名 |
| role | VARCHAR(20) | NO | 'admin' | admin 超级管理员 / operator 运营 / finance 财务 |
| status | TINYINT | NO | 1 | 1 启用 / 0 禁用 |
| last_login_at | DATETIME | YES | NULL | 最近登录 |
| created_at | DATETIME | NO | 当前时间 | — |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：`uk_username`（username）

### 3.16 会员会话表 `member_session`

> 微信登录成功后签发的登录态记录（C 端）。首版不引入 Redis，会话持久化到 MySQL；过期由 `expires_at` 惰性校验（到期即返回 401），每日定时任务兜底清理过期记录（见 architecture §5.6）。

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| user_id | BIGINT UNSIGNED | NO | — | 外键 member(id) |
| token | VARCHAR(64) | NO | — | 登录态 token（服务端安全随机串生成），唯一索引 |
| expires_at | DATETIME | NO | — | 过期时间（登录时间 + 7 天） |
| created_at | DATETIME | NO | 当前时间 | 登录时间 |
| updated_at | DATETIME | NO | 当前时间 | — |

索引：
- `uk_token`（token）
- `idx_user`（user_id）

> 同一用户可保留多个会话（多设备），退出登录时删除对应记录；封禁用户后删除全部会话即可立即失效。

### 3.17 系统配置表 `sys_config`

| 字段 | 类型 | 允许空 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | 自增 | 主键 |
| config_key | VARCHAR(64) | NO | — | 配置键，唯一 |
| config_value | TEXT | NO | — | 配置值（JSON 兼容） |
| remark | VARCHAR(255) | YES | NULL | 说明 |
| updated_at | DATETIME | NO | 当前时间 | — |

预留键示例：`service_hotline`（客服热线 400-800-8888）、`free_shipping_threshold`（包邮门槛）、`app_version`。

---

## 4. 初始化数据（种子数据）

上线初始化脚本 `docs/sql/` 需预置：

1. **分类**：鞋服 / 箱包 / 数码 / 美妆 / 家居（对应前端 `categories`）
2. **商品 + SKU**：按前端 `productCatalog` 10 条商品；SKU 组合按各商品 `attrs` 属性组笛卡尔积生成，示例商品快照：
   | 商品 | 价格 | 划线价 | 分类 | 颜色 | 尺码 |
   | --- | --- | --- | --- | --- | --- |
   | 潮流运动鞋 | 299 | 599 | 鞋服 | 云雾白/碳素黑/珊瑚粉 | 39-42 |
   | 轻便休闲鞋 | 199 | 359 | 鞋服 | 云雾白/碳素黑 | 38-43 |
   | 简约单肩包 | 159 | 329 | 箱包 | 棕色/黑色 | 均码 |
   | 无线降噪耳机 | 899 | 1299 | 数码 | 黑色 | 均码 |
   | 保湿护肤套装 | 219 | 399 | 美妆 | — | 礼盒装 |
   | 北欧风香薰套装 | 89 | 169 | 家居 | — | 均码 |
   | 复古水桶包 | 229 | 459 | 箱包 | 棕色/黑色 | 均码 |
   | 真无线蓝牙耳机 | 259 | 469 | 数码 | 白色/黑色 | 均码 |
   | 焕亮精华面膜 | 129 | 259 | 美妆 | — | 5片装 |
   | 云朵抱枕靠垫 | 69 | 129 | 家居 | 米白/浅灰 | 均码 |
3. **运营位**：hero 横幅 1 条 + 主题精选 4 条（夏季焕新/会员专享/通勤百搭/影音数码）
4. **系统配置**：`service_hotline = 400-800-8888`
5. **管理员**：初始账号（上线前必须修改密码）

---

## 5. 会话与缓存设计（首版不引入 Redis）

- **登录会话**：持久化到 MySQL，见 3.16 `member_session` 表；token 唯一，服务端按 `expires_at` 惰性校验过期（到期即返回 401），每日定时任务兜底清理过期记录，退出登录删除对应记录
- **业务缓存**：商品列表/详情、首页聚合、购物车首版均直接查 MySQL；待数据量或读压力上来后再引入缓存（预留迁移空间，勿在首版阻塞开发）
- **并发控制**：库存扣减、优惠券/积分发放依赖 MySQL 行锁与事务（见 §6），不依赖分布式锁

---

## 6. 数据一致性要点

1. **下单扣库存**：`status=pending` 预占库存（`lock_stock += qty`）；支付成功**转实扣**（`stock -= qty` 且 `lock_stock -= qty`）；订单超时未支付（如 2 小时）任务释放锁定（`lock_stock -= qty`）并关闭订单；退款（`refund`）**回补已实扣库存**（`stock += qty`）
2. **订单金额**：服务端以 `order_item.price × quantity` 汇总，禁止信任客户端上送金额
3. **地址快照**：下单时复制地址到 `orders` 表，后续修改地址不影响历史订单
4. **优惠券/积分**：参与金额计算时在事务内用 `SELECT ... FOR UPDATE`（MySQL 行锁）防并发超发
5. **逻辑删除**：`orders`/`shipping_address`/`member`/`product`/`product_sku` 启用 `deleted` 标志（三端一致，见 §1.3），`category`/`banner` 仅用 `status` 软开关；默认查询条件过滤