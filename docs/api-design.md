# 快乐购商城 - API 接口设计文档

> 项目：快乐购（自营私域商城小程序）
> 版本：v1.0（首个后端版本）
> 技术栈：Python 3.11+ + FastAPI + SQLAlchemy + MySQL 8（首版不引入 Redis）；RESTful 风格 + JSON
> 服务端入口：`/api`（生产建议 nginx 反代，HTTPS）

***

## 1. 通用约定

### 1.1 基础信息

| 项            | 约定                                                  |
| ------------ | --------------------------------------------------- |
| 协议           | HTTPS（生产）/ HTTP（本地联调）                               |
| Base URL     | `https://{host}/api`                                |
| Content-Type | `application/json; charset=utf-8`                   |
| 数据格式         | JSON（UTF-8）                                         |
| 时间格式         | 字符串 `yyyy-MM-dd HH:mm:ss`（北京时间，与前端 `formatTime` 一致） |
| 金额           | 服务端返回数字（元），如 `299.00`                               |

> **手机号脱敏口径（定稿）**：地址管理（§8）、下单预览/回执（§9.1/§9.2）、订单详情（§9.4）返回本人完整手机号（本人数据，物流联系/编辑核对需要）；脱敏仅适用于对外可见场景（后台列表、日志、匿名接口），日志脱敏见 [logging.md](conventions/logging.md)。

### 1.2 通用响应结构

所有接口统一返回：

```json
{
  "code": 0,
  "message": "ok",
  "data": { }
}
```

| 字段      | 类型                | 说明                      |
| ------- | ----------------- | ----------------------- |
| code    | int               | 业务码，0 表示成功，非 0 为业务/系统错误 |
| message | string            | 可读信息，成功为 `ok`，失败为错误描述   |
| data    | object/array/null | 业务数据，无数据时可为 `null`      |

分页数据统一封装：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "list": [],
    "total": 120,
    "page": 1,
    "pageSize": 10,
    "hasMore": true
  }
}
```

### 1.3 错误码

统一响应结构见 §1.2；**完整错误码定义见** **[conventions/error-code.md](conventions/error-code.md)**（模块分段式），本节仅列高频错误：

| code | 含义              | 说明                             |
| ---- | --------------- | ------------------------------ |
| 0    | 成功              | —                              |
| 400  | 参数错误            | 缺少参数或参数非法，`message` 指明具体字段     |
| 401  | 未登录/登录过期        | 需重新登录                          |
| 403  | 无权限             | 非本人资源或角色不足                     |
| 404  | 资源不存在           | ID 不存在或已删除                     |
| 409  | 业务冲突            | 如重复支付、订单状态冲突等                  |
| 429  | 请求过于频繁          | —                              |
| 500  | 系统内部错误          | —                              |
| 1001 | 登录 code 无效      | 微信 code2session 失败             |
| 1102 | 商品已下架           | —                              |
| 1104 | 库存不足            | `data` 返回可购买数量                 |
| 1201 | 数量超出单次限购（最大 99） | 购物车加购/改数量                      |
| 1203 | 结算商品含不可售项       | 结算预览（下架/库存为 0），`data` 携带不可售项列表 |
| 1402 | 订单状态不允许该操作      | 如取消已支付订单、对未发货订单确认收货            |

### 1.4 鉴权方式

- 登录后服务端签发 `token`，返回给客户端；客户端后续请求在 **Header** 携带：

```
Authorization: Bearer {token}
```

- token 有效期 7 天，会话记录保存至 `member_session` 表（见数据库设计 3.16）；过期返回 `401`，前端引导重新登录

- 需要登录的接口：购物车、地址、订单、收藏、会员中心等（标注 🔒）

- 商品、分类、首页等公开接口无需登录

### 1.5 参数与返回字段命名

- API 字段使用驼峰（与前端现有数据命名一致）；DB 字段为下划线，由后端 ORM 转换

- 分页参数统一：`page`（从 1 开始）、`pageSize`（默认 10，最大 50）

- 列表排序参数：`sort` + `order`（asc/desc）

***

## 2. 模块总览

| 模块   | 前缀                                    | 说明                    | 章节  |
| ---- | ------------------------------------- | --------------------- | --- |
| 认证   | `POST /api/auth/*`                    | 微信登录、退出               | §3  |
| 首页   | `GET /api/home/index`                 | 首页聚合（公开）              | §4  |
| 分类   | `GET /api/categories`                 | 商品分类（公开）              | §5  |
| 商品   | `GET /api/products*`                  | 列表、详情、搜索（公开）          | §6  |
| 购物车  | `GET/POST/PUT/DELETE /api/cart/*`     | 购物车 CRUD 🔒           | §7  |
| 地址   | `GET/POST/PUT/DELETE /api/addresses*` | 收货地址 CRUD 🔒          | §8  |
| 订单   | `POST/GET /api/orders*`               | 结算预览、下单、查询与操作 🔒      | §9  |
| 收藏   | `GET/POST/DELETE /api/favorites*`     | 收藏管理 🔒               | §10 |
| 会员   | `GET/PUT /api/member/*`               | 个人中心聚合、资料更新、优惠券、积分 🔒 | §11 |
| 售后   | `POST/GET /api/after-sales*`          | 售后申请（预留）🔒            | §12 |
| 管理后台 | `/admin/api/*`                        | 商品/订单/会员/运营位管理（独立鉴权）  | §13 |

***

## 3. 认证接口

### 3.1 微信登录

```
POST /api/auth/login
```

请求：

```json
{
  "code": "wx.login 返回的 code",
  "nickname": "选填，微信昵称",
  "avatar": "选填，微信头像"
}
```

响应 `data`：

```json
{
  "token": "eyJhbGciOi...",
  "expiresIn": 604800,
  "member": {
    "id": 1,
    "nickname": "快乐购物家",
    "avatar": "",
    "memberLevel": "bronze",
    "points": 0,
    "phone": ""
  }
}
```

业务规则：

- 后端用 `code` 调微信 `code2session` 换 `openid`；`openid` 不存在则自动注册新会员

- 首次登录返回 `member` 为新建会员，前端"快乐购物家"默认昵称

- 失败返回 `1001`

### 3.2 退出登录 🔒

```
POST /api/auth/logout
```

无请求体。成功 `code=0`，服务端清除会话；与其它 🔒 接口一致强制校验登录态，无/无效/过期 token 返回 `401`。

***

## 4. 首页接口

### 4.1 首页聚合

```
GET /api/home/index
```

响应 `data`：

```json
{
  "member": {
    "points": 0,
    "couponCount": 0,
    "nickname": "快乐购物家"
  },
  "banners": [
    { "id": 1, "title": "夏季新品 火热开售", "tag": "限时特惠", "image": "https://...", "linkType": "page", "linkValue": "/pages/products/products" }
  ],
  "themes": [
    { "id": 2, "name": "夏季焕新", "desc": "轻盈出行", "image": "https://...", "linkType": "category", "linkValue": "1" }
  ],
  "promises": ["正品保障", "7天无理由", "极速发货"]
}
```

- 公开接口；未登录时 `member` 返回 `null`，前端显示默认问候

- `banners` 对应 hero 主横幅，`themes` 对应轮播"主题精选"

***

## 5. 分类接口

### 5.1 分类列表

```
GET /api/categories
```

响应 `data`：

```json
{
  "list": [
    { "id": 1, "name": "鞋服", "sort": 1 },
    { "id": 2, "name": "箱包", "sort": 2 }
  ]
}
```

> 前端还需展示"全部"（value 0 / 不传 categoryId），由前端本地拼接即可。

***

## 6. 商品接口

### 6.1 商品列表（含搜索/分类/排序）

```
GET /api/products
```

Query 参数：

| 参数         | 类型     | 必填 | 说明                                      |
| ---------- | ------ | -- | --------------------------------------- |
| categoryId | int    | 否  | 分类 ID，不传为全部                             |
| keyword    | string | 否  | 搜索关键词（匹配名称/副标题），长度 ≤ 50                 |
| sort       | string | 否  | `default`（综合）/ `sales`（销量）/ `price`（价格） |
| order      | string | 否  | `asc` / `desc`，配合 sort，默认 desc          |
| page       | int    | 否  | 默认 1                                    |
| pageSize   | int    | 否  | 默认 10，最大 50                             |

响应 `data`：

```json
{
  "list": [
    {
      "id": 1,
      "productNo": "P20260831001",
      "name": "潮流运动鞋",
      "subTitle": "透气网面，轻弹缓震",
      "price": 299.00,
      "originalPrice": 599.00,
      "mainImage": "https://...",
      "sales": 12000,
      "tags": ["热销"]
    }
  ],
  "total": 10,
  "page": 1,
  "pageSize": 10,
  "hasMore": false
}
```

### 6.2 商品详情

```
GET /api/products/{id}
```

响应 `data`：

```json
{
  "id": 1,
  "productNo": "P20260831001",
  "categoryId": 1,
  "name": "潮流运动鞋",
  "subTitle": "透气网面，轻弹缓震",
  "price": 299.00,
  "originalPrice": 599.00,
  "mainImage": "https://...",
  "images": ["https://..."],
  "detailHtml": "<p>…</p>",
  "spec": { "材质": "织物+TPU", "闭合": "系带", "适用": "跑步/休闲", "产地": "中国" },
  "sales": 12000,
  "shippingFrom": "上海",
  "isFreeShipping": true,
  "tags": ["热销", "包邮"],
  "skus": [
    { "id": 10, "attrs": [{ "name": "颜色", "value": "云雾白" }, { "name": "尺码", "value": "40" }], "skuText": "云雾白；40", "price": 299.00, "stock": 88, "image": "" }
  ],
  "promises": ["正品保障", "7天无理由", "极速发货"]
}
```

- `skus` 为全部可售 SKU；`attrs` 为通用属性组数组（`name` + `value`），支持任意数量属性维度（如"颜色 × 尺码 × 款式"）；详情页弹层按 `attrs` 动态聚合属性组渲染

- `skus[].stock` 返回**可用库存**（`product_sku.stock - lock_stock`，对齐 §7.1 口径），前端弹层数量上限直接据此使用

- 商品下架统一返回 `1102`（业务可见性：下架商品不参与列表/详情返回）；仅商品 ID 不存在时返回 `404`

### 6.3 搜索建议（预留）

```
GET /api/products/search/hot
```

返回热词数组 `["运动鞋","耳机"]`，首版可不实现。

***

## 7. 购物车接口 🔒

### 7.1 购物车列表

```
GET /api/cart
```

响应 `data`：

```json
{
  "list": [
    {
      "id": 1,
      "productId": 1,
      "skuId": 10,
      "name": "城市慢跑鞋 透气轻盈",
      "skuText": "云雾白；40",
      "price": 299.00,
      "quantity": 1,
      "image": "https://...",
      "selected": true,
      "stock": 88,
      "onSale": true
    }
  ],
  "totalPrice": 299.00,
  "totalQuantity": 1
}
```

- `onSale=false` 表示该商品已下架：下架项**仍保留在购物车**中（前端置灰 + 标「已下架」），勾选后结算 preview 返回 `1203`（§8 结算预览）

- `totalPrice` / `totalQuantity` 仅统计**可售勾选项**：下架（`onSale=false`）或库存为 0 的项不计入

### 7.2 加入购物车

```
POST /api/cart/items
```

请求：

```json
{
  "skuId": 10,
  "quantity": 1,
  "selected": false
}
```

规则：

- 同一 SKU 已存在则数量累加

- `quantity` 范围 `1 ~ min(99, 可用库存)`：超出单次限购返回 `1201`，超出库存返回 `1104`（`data` 带最大可购数量）

- `selected` 默认 `false`（新增项默认**不勾选**，需用户在购物车手动勾选后参与结算）；「立即购买」走直购链路（§9.1），不改变购物车勾选态

### 7.3 修改购物车项

```
PUT /api/cart/items/{id}
```

请求（三个字段均可选，传哪个改哪个）：

```json
{
  "quantity": 2,
  "selected": false,
  "skuId": 12
}
```

规则：

- `quantity` 最小 1；减少至 0 视为删除（或前端显式删除）

- `skuId` 用于**修改规格**：仅允许切换到**同一商品**的其他 SKU（跨商品返回 `400`）；若目标 SKU 已在购物车，则数量累加并移除原项；否则更新该购物车项的 `skuText`/`price`/`stock`，并校验新 SKU 库存（`1104`）

- 对应前端 `cart.vue` 点击购物车项规格文字弹出修改规格弹层

### 7.4 删除购物车项

```
DELETE /api/cart/items/{id}
```

### 7.5 批量删除

```
DELETE /api/cart/items
```

请求：

```json
{ "ids": [1, 2, 3] }
```

### 7.6 全选/取消全选

```
PUT /api/cart/select-all
```

请求：

```json
{ "selected": true }
```

- `selected: true`（全选）：仅操作**可售项**——下架（`onSale=false`）或库存为 0 的购物车项不参与全选

- `selected: false`（取消全选）：清空**全部**勾选（含失效项），保证"立即购买"直购链路（§9.1）不受历史勾选态干扰

***

## 8. 收货地址接口 🔒

### 8.1 地址列表

```
GET /api/addresses
```

响应 `data`：

```json
{
  "list": [
    {
      "id": 1,
      "name": "王小悦",
      "phone": "13812345678",
      "province": "上海市",
      "city": "上海市",
      "district": "浦东新区",
      "detail": "张江高科技园区 1 号楼 501 室",
      "isDefault": true,
      "regionText": "上海市 上海市 浦东新区"
    }
  ]
}
```

- 按 `isDefault` 优先、创建时间倒序返回

- `regionText` 为 `省 市 区` 拼接串，前端直接展示

### 8.2 新增地址

```
POST /api/addresses
```

请求：

```json
{
  "name": "王小悦",
  "phone": "13812345678",
  "province": "上海市",
  "city": "上海市",
  "district": "浦东新区",
  "detail": "张江高科技园区 1 号楼 501 室",
  "isDefault": true
}
```

- 校验：姓名非空、手机号 `^1\d{10}$`、省市区与详细地址非空

- 数量上限：同用户地址最多 20 条，超出返回 `1301`（`data` 带 `maxCount`）

- `isDefault=true` 时服务端将其他地址默认标识置 0（同用户唯一默认）

- 用户首个地址自动置为默认（与前端 `address-edit.vue` 逻辑一致）

- 响应 `data` 为单个地址对象（含 `regionText`）

### 8.3 编辑地址

```
PUT /api/addresses/{id}
```

请求体同新增（全部字段必传，整体覆盖）。

- 响应 `data` 为单个地址对象（含 `regionText`）

### 8.4 删除地址

```
DELETE /api/addresses/{id}
```

逻辑删除；删除默认地址后，若存在剩余地址，服务端将最新一条置为默认。

- 响应 `data` 为最新地址列表 `{list: [...]}`（结构同 §8.1）

### 8.5 设为默认

```
PUT /api/addresses/{id}/default
```

无请求体。

- 响应 `data` 为最新地址列表 `{list: [...]}`（结构同 §8.1）

***

## 9. 订单接口 🔒

### 9.1 结算预览（确认订单页加载）

```
GET /api/orders/preview
```

Query 参数：

| 参数          | 类型     | 必填 | 说明                      |
| ----------- | ------ | -- | ----------------------- |
| cartItemIds | string | 否  | 逗号分隔的购物车项 ID；不传默认取全部勾选项 |

响应 `data`：

```json
{
  "items": [
    {
      "cartItemId": 1,
      "productId": 1,
      "skuId": 10,
      "name": "城市慢跑鞋 透气轻盈",
      "skuText": "云雾白；40",
      "price": 299.00,
      "quantity": 1,
      "image": "https://...",
      "stock": 88
    }
  ],
  "totalAmount": 299.00,
  "freight": 0.00,
  "payAmount": 299.00,
  "addresses": [
    {
      "id": 3,
      "name": "王小悦",
      "phone": "13812345678",
      "regionText": "上海市 上海市 浦东新区",
      "detail": "张江…501 室",
      "isDefault": true
    }
  ]
}
```

业务规则：

- 服务端从购物车项核价（**不信任客户端价格**），金额口径与下单一致，支撑 `order-confirm.vue` 加载即渲染

- 商品已下架或可用库存为 0 → 返回 `1203`，`data` 携带不可售项列表

- 库存不足 → 返回 `1104` 并带上 `{ skuId, availableStock }`

- 勾选项为空 → 返回 `400`（前端引导回首页加购）

- 地址列表返回本人完整手机号（本人数据，脱敏口径见 §1.1）；无地址时前端引导新增

#### 直购（"立即购买"）口径

商品详情页"立即购买"使用**专用直购接口**，不经过购物车，实现"只结算本次商品"：

1. `GET /api/orders/preview-direct?skuId={id}&quantity={n}` —— 直购结算预览（返回单商品明细 + 地址列表）
2. `POST /api/orders/direct` `{ "addressId": 3, "skuId": 10, "quantity": 1 }` —— 直购下单（不写购物车、不删除购物车项）

对应前端 `product-detail.vue` 的 `buyNow` 与 `order-confirm.vue` 的 `directSkuId` 分支。直购链路**不触碰购物车勾选态**，与购物车结算完全隔离。

### 9.2 创建订单（确认订单页）

```
POST /api/orders
```

请求：

```json
{
  "addressId": 3,
  "items": [
    { "skuId": 10, "quantity": 1 },
    { "skuId": 12, "quantity": 2 }
  ],
  "userCouponId": 100,
  "pointsUsed": 100
}
```

- `userCouponId`（可选）：核销的用户券 ID；`pointsUsed`（可选）：积分抵扣数量（100 积分抵 1 元）

- 券/积分抵扣金额**由服务端核算**（不信任客户端），见下方业务规则

响应 `data`：

```json
{
  "id": 10001,
  "orderNo": "K20260831091512345",
  "status": "pending",
  "items": [
    {
      "id": 9001,
      "productName": "城市慢跑鞋 透气轻盈",
      "skuText": "云雾白；40",
      "price": 299.00,
      "quantity": 1,
      "image": "https://..."
    }
  ],
  "totalAmount": 299.00,
  "freight": 0.00,
  "couponAmount": 20.00,
  "pointsUsed": 100,
  "payAmount": 278.00,
  "receiver": { "name": "王小悦", "phone": "13812345678", "regionText": "上海市 上海市 浦东新区", "detail": "张江…501 室" }
}
```

业务规则：

- 服务端从购物车/商品核价（**不信任客户端价格**），创建订单为 `pending`

- 服务端写订单与明细、地址快照、预占库存（`lock_stock += qty`），同一事务

- 下单成功即删除本次订单涉及的购物车项（幂等；`order-confirm.vue` 本地清理 `mall-checkout-items` 与后端行为一致，前端购物车页无需额外处理）

- 缺货返回 `1104` 并带上 `{ skuId, availableStock }`

- 券/积分抵扣：`userCouponId` 校验（券不存在/非本人/非 unused → `1601`；停用/未生效/过期 → `1603`；不满足门槛 → `1604`）；`pointsUsed` 校验（积分不足 → `1605`）；核销券置 `used`、扣减积分并写 `points_log`（consume）

### 9.3 订单列表

```
GET /api/orders
```

Query 参数：

| 参数       | 类型     | 必填 | 说明                                                   |
| -------- | ------ | -- | ---------------------------------------------------- |
| status   | string | 否  | 空=全部；pending/paid/shipped/completed/refund/cancelled |
| page     | int    | 否  | 默认 1                                                 |
| pageSize | int    | 否  | 默认 10                                                |

响应 `data`：

```json
{
  "list": [
    {
      "id": 10001,
      "orderNo": "K20260831091512345",
      "status": "pending",
      "statusText": "待付款",
      "totalAmount": 299.00,
      "freight": 0.00,
      "couponAmount": 0.00,
      "pointsUsed": 0,
      "payAmount": 299.00,
      "createTime": "2026-08-31 09:15:12",
      "items": [
        { "id": 9001, "productName": "城市慢跑鞋…", "skuText": "云雾白；40", "price": 299.00, "quantity": 1, "image": "https://..." }
      ],
      "itemCount": 1,
      "availableActions": ["pay", "cancel"]
    }
  ],
  "total": 3,
  "page": 1,
  "pageSize": 10,
  "hasMore": false
}
```

- `statusText` 映射：pending 待付款 / paid 待发货 / shipped 待收货 / completed 已完成 / refund 售后中 / cancelled 已取消

- `availableActions` 由服务端按状态计算（pay/cancel/remind/confirm/refund/buyAgain），前端据此渲染按钮，避免前端硬编码状态机（对应 `orders.vue`）；各状态动作集：pending\[pay/cancel/buyAgain]、paid\[remind/refund/buyAgain]、shipped\[confirm/refund/buyAgain]、completed\[refund/buyAgain]、cancelled/refund\[buyAgain]

### 9.4 订单详情

```
GET /api/orders/{id}
```

响应 `data`：

```json
{
  "id": 10001,
  "orderNo": "K20260831091512345",
  "status": "pending",
  "statusText": "待付款",
  "statusDesc": "订单已提交，请尽快完成支付",
  "totalAmount": 299.00,
  "freight": 0.00,
  "payAmount": 299.00,
  "receiver": { "name": "王小悦", "phone": "13812345678", "regionText": "上海市 上海市 浦东新区", "detail": "张江…501 室" },
  "items": [ /* 同列表 */ ],
  "payType": null,
  "payTime": null,
  "shipTime": null,
  "finishTime": null,
  "createTime": "2026-08-31 09:15:12",
  "availableActions": ["pay", "cancel"]
}
```

- `statusDesc` 文案由服务端下发（对应前端 `statusDescMap`，避免两端文案漂移）

- `availableActions` 同 §9.3，按状态计算（含 refund）；订单详情页 `order-detail.vue` 据此渲染底部操作按钮

### 9.5 支付订单

```
POST /api/orders/{id}/pay
```

请求：

```json
{ "payType": "mock" }
```

- `mock`：联调模式，直接置 `paid`（对应前端当前模拟支付）

- 支付成功（含 `mock`）同时**库存转实扣**：`product_sku.stock -= qty` 且 `lock_stock -= qty`（下单时已预占 `lock_stock`，支付后实扣可售库存；对齐 §9.2 口径）

- `wechat`（预留）：返回 `{ "payParams": { "timeStamp": "…", "nonceStr": "…", "package": "…", "signType": "RSA", "paySign": "…" } }`，前端 `wx.requestPayment` 后回调通知

- 重复支付返回 `409`

### 9.6 取消订单

```
POST /api/orders/{id}/cancel
```

请求：

```json
{ "reason": "不想要了" }
```

- 仅 `pending` 可取消；取消后释放锁定库存（`lock_stock -= qty`，恢复可用库存）

- 取消成功后订单保留在列表中，前端以 `cancelled`（已取消）状态展示

### 9.7 申请售后/退款

```
POST /api/orders/{id}/refund
```

请求：

```json
{
  "reason": "不符合预期",
  "type": "refund"
}
```

| 参数     | 类型     | 必填 | 说明                                                              |
| ------ | ------ | -- | --------------------------------------------------------------- |
| reason | string | 否  | 申请原因，默认「不符合预期」                                                  |
| type   | string | 否  | `refund` 仅退款 / `return` 退货退款；不传时 paid 默认 `refund`，其余默认 `return` |

响应 `data`：同 §9.4 订单详情 DTO（状态已变更为 `refund`）。

业务规则：

- 仅 `paid` / `shipped` / `completed` 可申请售后；非三态返回 `1402`

- 申请后订单状态置 `refund`，**回补已实扣库存**（`stock += qty`；支付已转实扣，退款恢复可售），订单暂停流转

- 按钮文案由前端按原状态区分：paid「取消并退款」、shipped「退货退款」、completed「申请售后」（对应 `orders.vue` / `order-detail.vue` `refundLabel`）

- 售后完成后仅保留 `buyAgain` 动作；售后角标（`orderStats.refund`）同步 +1

- 完整售后工单（审核/退货物流/退款金额）为 P1 预留，见 §12

### 9.8 提醒发货

```
POST /api/orders/{id}/remind
```

- 仅 `paid`（待发货）可调用；返回 `{ "reminded": true }`

- 非 `paid` 状态返回 `1402`（对应前端 `orders.vue` / `order-detail.vue` 的 `remindShip`）

### 9.9 确认收货

```
POST /api/orders/{id}/confirm
```

- 仅 `shipped` 可调用；置 `completed`、记 `finish_time`，发放积分（按实付金额取整）并写 `points_log`（earn）

### 9.10 再次购买

```
POST /api/orders/{id}/buy-again
```

- 用订单 `items`（skuId）重新创建一笔 `pending` 订单并返回新订单（对应前端 `buyAgain`，但真正的再次购买 = 重新下单，而非把快照塞回结算页）

### 9.11 订单状态角标（我的页）

```
GET /api/orders/stats
```

响应 `data`：

```json
{
  "pending": 1,
  "paid": 1,
  "shipped": 2,
  "refund": 0
}
```

对应前端 `me.vue` 待付款/待发货角标。

***

## 10. 收藏接口 🔒

### 10.1 收藏列表

```
GET /api/favorites
```

Query：`page`、`pageSize`。

响应 `data`：

```json
{
  "list": [
    { "id": 1, "productId": 1, "name": "潮流运动鞋", "price": 299.00, "image": "https://..." }
  ],
  "total": 3,
  "page": 1,
  "pageSize": 10,
  "hasMore": false
}
```

### 10.2 添加收藏

```
POST /api/favorites/{productId}
```

幂等（定稿）：重复收藏返回成功（`200`），服务端按 `member + product` 唯一约束去重，不返回 `409`。

响应 `data`：

```json
{ "favorited": true, "existed": false }
```

- `existed`：本次收藏前是否已存在（重复收藏为 `true`，不新增记录）

- 商品不存在：`404`；商品已下架：`1102`「商品已下架」（对应 test-cases B6-2）

### 10.3 取消收藏

```
DELETE /api/favorites/{productId}
```

幂等移除：未收藏时同样返回成功。响应 `data`：

```json
{ "favorited": false }
```

***

## 11. 会员中心接口 🔒

### 11.1 会员概览（我的页聚合）

```
GET /api/member/overview
```

响应 `data`：

```json
{
  "member": {
    "id": 1,
    "nickname": "快乐购物家",
    "avatar": "",
    "memberLevel": "bronze",
    "memberLevelText": "普通会员",
    "points": 0,
    "couponCount": 0
  },
  "orderStats": { "pending": 1, "paid": 1, "shipped": 2, "refund": 0 }
}
```

- `couponCount`：当前用户**未使用**优惠券数量（真实统计，非恒 0）

### 11.2 会员资料更新（P0，对应 PRD §3.1 一期"头像昵称完善"）

```
PUT /api/member/profile
```

请求：

```json
{
  "nickname": "快乐购物家",
  "avatar": "https://cdn.example.com/avatars/xxx.jpg"
}
```

响应 `data`：

```json
{ "nickname": "快乐购物家", "avatar": "https://cdn.example.com/avatars/xxx.jpg" }
```

业务规则（对应 PRD §4.9 合规规则，P0 口径）：

- 头像：**P0 校验** **`http(s)`** **URL 即可**（无上传接口，微信登录头像为第三方 CDN 域名）；自有存储域白名单校验（先走上传接口）随上传接口上线后收紧，见 `docs/known-issues.md` 条目

- 昵称：长度 1-20 字返回 `1003`；敏感词过滤 P0 暂无词库暂不启用（见 `docs/known-issues.md` 条目）

- 仅可更新本人资料；成功后同步 `member` 表并返回最新资料

***

### 11.3 优惠券列表

```
GET /api/coupons?status=unused
```

Query 参数：

| 参数       | 类型     | 必填 | 说明                                       |
| -------- | ------ | -- | ---------------------------------------- |
| status   | string | 否  | 空=全部；unused 未使用 / used 已使用 / expired 已过期 |
| page     | int    | 否  | 默认 1                                     |
| pageSize | int    | 否  | 默认 10                                    |

响应 `data`：

```json
{
  "list": [
    {
      "id": 100,
      "couponId": 1,
      "name": "满100减20",
      "type": "cash",
      "amount": 20.00,
      "discount": null,
      "minAmount": 100.00,
      "status": "unused",
      "validStart": "2026-09-01 00:00:00",
      "validEnd": "2026-12-31 23:59:59"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 10,
  "hasMore": false
}
```

- `type`：cash 满减 / discount 折扣 / shipping 免运费；`amount` 满减金额（cash 用）、`discount` 折扣率（discount 用）

### 11.3a 领取优惠券

```
POST /api/coupons/{couponId}/receive
```

响应 `data`：

```json
{ "userCouponId": 100, "existed": false }
```

业务规则：

- 券不存在 → `1601`；已领取 → `1602`（幂等返回 `existed=true`）

- 券停用/未到生效期/已过期/已领完 → `1603`

- 领取成功 `received_count + 1`，生成 `unused` 用户券

### 11.4 积分明细

```
GET /api/points-logs?page=1&pageSize=20
```

响应 `data`：

```json
{
  "list": [
    {
      "id": 1,
      "change": 100,
      "balance": 100,
      "type": "earn",
      "bizType": "order",
      "remark": "订单完成获得积分",
      "createdAt": "2026-09-01 10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20,
  "hasMore": false
}
```

- `type`：earn 获得 / consume 消费 / refund 退回；`bizType`：order/promotion/admin

***

## 12. 售后接口 🔒（预留，首版可不实现）

### 12.1 申请售后

```
POST /api/after-sales
```

请求：

```json
{
  "orderId": 10001,
  "type": "refund",
  "reason": "商品破损",
  "images": ["https://..."]
}
```

### 12.2 售后单列表/详情（预留）

```
GET /api/after-sales?status=applying
GET /api/after-sales/{id}
```

***

## 13. 管理后台接口（规划）🔒

鉴权：`POST /admin/api/login`（username + password → JWT），后续请求带 `Authorization: Bearer {token}`；角色：admin / operator / finance。

| 模块  | 接口                                                                                     | 说明                 |
| --- | -------------------------------------------------------------------------------------- | ------------------ |
| 商品  | `GET/POST /admin/api/products`、`PUT/DELETE /admin/api/products/{id}`                   | 商品 CRUD、上下架、SKU 维护 |
| 分类  | `GET/POST/PUT/DELETE /admin/api/categories`                                            | 分类管理               |
| 订单  | `GET /admin/api/orders`、`GET /admin/api/orders/{id}`、`PUT /admin/api/orders/{id}/ship` | 查询、发货              |
| 售后  | `GET /admin/api/after-sales`、`PUT /admin/api/after-sales/{id}/audit`                   | 审核                 |
| 会员  | `GET /admin/api/members`、`PUT /admin/api/members/{id}/status`                          | 列表、禁用              |
| 运营位 | `GET/POST/PUT/DELETE /admin/api/banners`                                               | 首页横幅/主题管理          |
| 优惠券 | `GET/POST/PUT /admin/api/coupons`、`POST /admin/api/coupons/{id}/grant`                 | 券模板与发放             |
| 数据  | `GET /admin/api/dashboard/summary`                                                     | 销售额、订单量、用户数概览      |
| 设置  | `GET/PUT /admin/api/configs`                                                           | 系统配置               |

***

## 14. 接口优先级与版本计划

### P0（必须，对接现有页面，除预留外全部实现）

1. 认证：微信登录（可先 mock：`code` 任意值 + 本地生成 openid）
2. 首页聚合、分类、商品列表/详情/搜索
3. 购物车 6 个接口
4. 地址 5 个接口
5. 订单 13 个接口（含结算预览、直购预览/下单、售后/退款、提醒发货；支付先用 `mock`）
6. 收藏 3 个接口
7. 会员概览、会员资料更新（`PUT /api/member/profile`）

### P1（下个迭代）

微信支付（`wechat`）、订单超时关闭任务、售后、优惠券、积分流水、管理后台全部接口。

***

## 15. 边界与风险

| 场景                                           | 建议                                                                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 前端目前购物车/订单存在本地，切后端后需**一次性迁移**                | 首版不做数据迁移，本地数据可丢弃                                                                                             |
| 前端 `products.vue` 的"加入购物车"仅 toast 未真正入车      | **~~必修项~~**~~：接入~~ ~~`POST /api/cart/items`（默认取首个 SKU）~~ **已解决**：`products.vue`/`product-detail.vue` 已接入真实加购 |
| `product-detail.vue` 的 SKU 弹层已按 `attrs` 动态渲染 | 已实现：属性组由 `/api/products/{id}` 返回的 `skus[].attrs` 聚合，支持任意维度                                                   |
| 收藏页当前是写死数组                                   | **必修项**：改调 `/api/favorites`                                                                                  |
| `me.vue` 会员数据（积分/券/等级/昵称）为写死                 | **必修项**：改调 `/api/member/overview`                                                                            |
| 订单号 `K202608301420` 前缀 `K`                   | 服务端保留 `K+yyyyMMddHHmmss+3位随机` 生成规则即可兼容展示                                                                     |
| 支付回调与退款                                      | 依赖微信商户号资质，未开通前用 `mock`                                                                                       |
| 金额展示 `¥` 由前端处理                               | 接口只回数字，不返回货币符号                                                                                               |
| `me.vue` 我的页角标跳转订单页传 `1/2/3/4` 数字 tab        | **必修项**：改为订单状态字符串（pending/paid/...）作为 `status` 参数                                                            |
| `order-confirm.vue` 进入页面即 `createOrder` 落单   | **必修项**：改为先调结算预览（`GET /api/orders/preview`），仅确认提交时才创建订单                                                      |
| 地址表单为 `region` 数组（省/市/区）                     | **必修项**：提交时拆分映射为 `province/city/district` 字段，展示用 `regionText`                                                |
| 取消订单当前为 `removeOrder` 删除                     | **必修项**：保留订单并以 `cancelled` 状态展示；前端 `statusMap`/`statusDescMap` 补充 `cancelled`                                |
| `buyAgain` 当前把快照塞回结算页                        | **必修项**：改为调 `POST /api/orders/{id}/buy-again` 重新下单                                                           |

***

## 16. 前端 Mock 核对结论（契约核对记录）

> 本记录用于"前端先用 mock 核对 API 文档，再开发后端"流程的交付物。前端 mock 已按本文档全量实现并逐页面打通，以下为核对过程中补充/澄清的口径，后端实现时应与本文档保持一致。

### 16.1 覆盖范围与仿真深度

- Mock 位于 `mall-miniapp-uni/src/api/mock/`（`store.js` 状态+业务、`routes.js` 路由、`index.js` 出口），经 `src/api/request.js` 的 `mockRequest` 先行分流；`config.js` 的 `useMock` 可一键切换真实后端。

- 覆盖本文档 §3\~§11 全部已实现接口，对接 12 个前端页面。

- 全仿真行为：登录/退出 token 生命周期（7 天有效期）、订单状态机（pending→paid→shipped→completed，pending→cancelled，paid/shipped/completed→refund 分支）、`availableActions` 动态计算（含 refund）、库存预占与回补（下单锁库存，取消/退款释放锁定；**mock 层未建模"支付转实扣"**，真实后端为支付实扣 + 退款回补已实扣库存，差异见 known-issues #6）、幂等收藏（同商品重复收藏返回既有记录）、下单后删除本次购物车项。

### 16.2 核对补充/澄清的口径

| # | 事项                       | 结论                                                                                                        |
| - | ------------------------ | --------------------------------------------------------------------------------------------------------- |
| 1 | 商品详情"立即购买"               | 已实现**专用直购接口**（§9.1 直购口径）：`GET /api/orders/preview-direct` + `POST /api/orders/direct`，不经过购物车、不触碰勾选态       |
| 2 | 确认订单页与地址页间"选中地址"传递       | 前端本地 storage 键 `checkoutAddressId` 传递地址 id，**无对应接口**；后端仅需保证 `preview` 返回完备 `addresses` 列表且含 `isDefault`   |
| 3 | `/api/orders/stats` 角标口径 | 只统计 `pending/paid/shipped/refund` 四态；`completed/cancelled` 不进角标（与 `me.vue` 布局一致）                          |
| 4 | 订单列表分页                   | `orders.vue` 首版一次性拉取 `page:1&pageSize:50`，未做滚动分页；`list/total/page/pageSize/hasMore` 分页契约已按本文档实现，后续增强无需改接口 |
| 5 | `settings.vue` 退出登录      | 已接入 `POST /api/auth/logout`；服务端只需清 token，无额外业务数据清理要求                                                      |
| 6 | 直购后购物车勾选态                | 下单成功即删除本次购物车项（§9.2），勾选态自然为空，前端无需额外处理                                                                      |

### 16.3 错误码实测路径

| 错误码         | 触发场景（mock 实测）                                                               |
| ----------- | --------------------------------------------------------------------------- |
| 401         | 未登录或 token 过期（7 天）调用需鉴权接口；页面捕获后提示重新登录                                       |
| 400         | 勾选项为空结算预览、订单商品为空、地址参数不合法、无需结算商品的 `buy-again`                                |
| 404         | SKU/商品/购物车项/地址/订单不存在                                                        |
| 409         | 对已支付订单重复支付（幂等冲突），前端提示"订单已支付"                                                |
| 1001 / 1003 | 登录 code 无效；昵称长度或头像 URL 非法                                                   |
| 1102        | 单商品已下架不可加购                                                                  |
| 1104        | 库存不足（`addItem`/`preview`/`create` 均校验，`data` 带 `{ skuId, availableStock }`） |
| 1201        | 数量超出单次限购 99（`data` 带 `{ maxQuantity }`）                                     |
| 1203        | `preview` 检测到部分商品已下架/不可售（`data` 带 `unavailables` 列表）                        |
| 1402        | 订单状态不允许该操作（如已取消订单取消、未发货提醒发货）                                                |

### 16.4 留给后端的实现提示

- `POST /api/orders` 必须同一事务完成：订单 + 明细 + 地址快照 + 库存预占（`lock_stock += qty`）+ 删除本次购物车项

- 直购接口（`preview-direct`/`direct`）不写购物车、不删除购物车项，仅做单商品核价 + 下单（§9.1 直购口径）

- 库存预占/结转：`pending` 下单即预占（`lock_stock += qty`）；取消或超时未支付释放锁定（`lock_stock -= qty`）；支付成功转实扣（`stock`/`lock_stock` 双扣）；退款（refund）回补已实扣库存（`stock += qty`）

- `availableActions` 由服务端按状态计算返回，前端不做状态机硬编码（§9.3）

- 时间统一 `yyyy-MM-dd HH:mm:ss`；金额为数字（元），不返回货币符号

