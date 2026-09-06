# 快乐购商城 - WebSocket 实时推送需求文档

> 项目：快乐购（自营私域商城小程序）
> 版本：v1.0
> 状态：待评审
> 范围：仅 WebSocket 实时推送，不含微信订阅消息（二期再做）

***

## 1. 需求背景与目标

### 1.1 背景

当前小程序、后端、后台可视化三者采用"请求-响应"（pull）模式：后端数据变化后，小程序和后台必须**重新发起请求**才能拿到最新数据，无法自动感知更新。

### 1.2 目标

实现"后端数据一变 → 主动推送信号 → 前端自动刷新"，消除手动刷新页面的操作。

### 1.3 核心原则

- **推送只发"事件信号"，不携带完整业务数据**；前端收到信号后复用现有 `load()`/`reload()` 重新拉取。

- 所有**读接口、页面模板、业务逻辑、数据库结构**均不修改。

- 复用现有登录鉴权体系，不新增登录机制。

***

## 2. 范围

### 2.1 本期范围（WebSocket）

| 端   | 能力                              |
| --- | ------------------------------- |
| 后端  | 提供 WebSocket 服务端，业务写操作后主动推送事件信号 |
| 后台  | 建立 WebSocket 连接，收到信号后自动刷新对应页面   |
| 小程序 | 建立 WebSocket 连接，收到信号后自动刷新对应页面   |

### 2.2 非本期范围

- 微信订阅消息（服务通知）——二期再做

- 用户不在线时的离线触达——依赖订阅消息，本期不做

- 会员/管理员管理页面的实时刷新——低频、无强实时需求，不做

***

## 3. 总体架构

```
┌──────────────┐   REST(读)    ┌──────────────┐
│  后台 Vue     │ ────────────▶ │              │
│  (WebSocket) │ ◀──────────── │  后端 FastAPI │
└──────────────┘  WS 推送信号   │  (WS 服务端)  │
┌──────────────┐   REST(读)    │              │
│  小程序 uni   │ ────────────▶ │              │
│  (WebSocket) │ ◀──────────── │              │
└──────────────┘  WS 推送信号   └──────────────┘
```

### 3.1 主题（Topic）设计

| 主题                | 订阅方      | 推送内容                          |
| ----------------- | -------- | ----------------------------- |
| `admin`           | 后台所有页面   | 新订单、订单变化、售后变化、商品/分类/横幅/券/配置变化 |
| `public`          | 所有小程序用户  | 运营数据变化（商品/分类/横幅/券/配置）         |
| `order:{user_id}` | 单个会员的小程序 | 该会员的订单状态变化                    |

### 3.2 事件（Event）清单

| 事件                   | 含义     | 触发方                   |
| -------------------- | ------ | --------------------- |
| `order_new`          | 产生新订单  | 用户下单/再次购买             |
| `order_changed`      | 订单状态变化 | 支付/取消/确认收货/发货/售后/超时关闭 |
| `after_sale_changed` | 售后单变化  | 申请售后/审核售后             |
| `catalog_changed`    | 运营数据变化 | 商品/分类/横幅/券/配置变更       |

***

## 4. 后端需求

### 4.1 新增连接管理器（`app/core/ws.py`）

- 按主题维护 WebSocket 连接集合。

- 提供 `connect` / `disconnect` / `send_to_topic` 异步能力。

- 提供 `notify(topic, event, payload)` 同步入口：供同步 service 层调用，异步提交到事件循环，**不阻塞业务事务**。优先使用当前运行中的事件循环；若在同步 `def`（线程池）中调用则回退到主事件循环（`run_coroutine_threadsafe`）。

- 提供 `notify_threadsafe(topic, event, payload)` 线程安全入口：供定时任务（独立线程）调用，需获取主事件循环或使用线程安全方式提交。

### 4.2 新增 WebSocket 路由（`app/api/v1/ws.py`）

| 端点           | 订阅方 | 鉴权                                                                                    |
| ------------ | --- | ------------------------------------------------------------------------------------- |
| `/admin/ws`  | 后台  | 首条消息发 `admin_token`，`decode_admin_jwt` 校验，绑定 `admin` 主题                               |
| `/ws/member` | 小程序 | 首条消息发 `mall-token`，查 `member_session` 解析 `user_id`，绑定 `order:{user_id}` + `public` 主题 |

- 连接建立后，首条消息必须是 `{type:'auth', token}`，校验通过才绑定主题。

- 鉴权失败则关闭连接。

- 支持心跳/保活（`receive_text` 循环）。

### 4.3 注册路由（`app/api/v1/router.py`）

- 将 ws 路由挂载到 `api_router`。

### 4.4 业务写操作埋点

在以下**写操作** **`db.commit()`** **之后**调用 `notify(...)`：

| 文件                      | 函数                              | 事件                                     | 主题                          |
| ----------------------- | ------------------------------- | -------------------------------------- | --------------------------- |
| `order/service.py`      | `create_order`                  | `order_new`                            | `admin`                     |
| `order/service.py`      | `create_order`                  | `order_changed`                        | `order:{user_id}`           |
| `order/service.py`      | `create_direct_order`           | `order_new`                            | `admin`                     |
| `order/service.py`      | `create_direct_order`           | `order_changed`                        | `order:{user_id}`           |
| `order/service.py`      | `pay_order`                     | `order_changed`                        | `order:{user_id}` + `admin` |
| `order/service.py`      | `cancel_order`                  | `order_changed`                        | `order:{user_id}` + `admin` |
| `order/service.py`      | `confirm_order`                 | `order_changed`                        | `order:{user_id}` + `admin` |
| `order/service.py`      | `buy_again`                     | `order_new` + `order_changed`          | `admin` + `order:{user_id}` |
| `order/service.py`      | `close_timeout_orders`          | `order_changed`                        | `order:{user_id}`           |
| `admin/service.py`      | `ship_order`                    | `order_changed`                        | `order:{user_id}` + `admin` |
| `admin/service.py`      | `audit_after_sale`              | `order_changed` + `after_sale_changed` | `order:{user_id}` + `admin` |
| `admin/service.py`      | `create/update/delete_product`  | `catalog_changed`                      | `admin` + `public`          |
| `admin/service.py`      | `create/update/delete_category` | `catalog_changed`                      | `admin` + `public`          |
| `admin/service.py`      | `create/update/delete_banner`   | `catalog_changed`                      | `admin` + `public`          |
| `admin/service.py`      | `create/update_coupon`          | `catalog_changed`                      | `admin` + `public`          |
| `admin/service.py`      | `update_config`                 | `catalog_changed`                      | `admin` + `public`          |
| `after_sale/service.py` | `create_after_sale`             | `after_sale_changed` + `order_changed` | `admin` + `order:{user_id}` |

> 注：`close_timeout_orders` 由定时任务在独立线程调用，需使用 `notify_threadsafe`。

### 4.5 鉴权

| 端   | 连接地址                  | 鉴权方式                                                                               |
| --- | --------------------- | ---------------------------------------------------------------------------------- |
| 后台  | `ws://host/admin/ws`  | 首条消息发 `admin_token`，`decode_admin_jwt` 校验                                          |
| 小程序 | `ws://host/ws/member` | 首条消息发 `mall-token`，查 `member_session` 解析 `user_id`，绑定 `order:{user_id}` + `public` |

**安全要求**：主题隔离，`order:{user_id}` 只推给该会员，`admin` 只推给后台，`public` 只推运营数据（不含订单等隐私数据），避免越权。

***

## 5. 后台需求（mall-admin）

### 5.1 新增 WebSocket 客户端（`src/utils/ws.js`）

- 单例连接，连接地址 `ws://host/admin/ws`（同源，`location.host`）。

- 连接建立后发送 `{type:'auth', token}`（token 取 `localStorage['admin_token']`）。

- 按事件分发回调（`onWS(event, fn)`）。

- 断线后 3 秒自动重连。

### 5.2 连接生命周期（`src/layout/Index.vue`）

- 登录后（`onMounted`）调用 `connectWS()`。

- 退出登录时断开连接。

### 5.3 页面订阅刷新

| 页面               | 订阅事件                          | 回调     |
| ---------------- | ----------------------------- | ------ |
| `Dashboard.vue`  | `order_new`、`catalog_changed` | `load` |
| `Orders.vue`     | `order_new`、`order_changed`   | `load` |
| `AfterSales.vue` | `after_sale_changed`          | `load` |
| `Products.vue`   | `catalog_changed`             | `load` |
| `Categories.vue` | `catalog_changed`             | `load` |
| `Banners.vue`    | `catalog_changed`             | `load` |
| `Coupons.vue`    | `catalog_changed`             | `load` |
| `Configs.vue`    | `catalog_changed`             | `load` |

> 后台 API 前缀为 `/admin/api`，WebSocket 走 `/admin/ws`，复用 vite 现有 `/admin` 代理规则。

***

## 6. 小程序需求（mall-miniapp-uni）

### 6.1 新增 WebSocket 客户端（`src/api/ws.js`）

- 单例连接，连接地址 `ws://host/ws/member`（`BASE_URL` 的 `http` → `ws`）。

- 连接建立后发送 `{type:'auth', token}`（token 取 `uni.getStorageSync(TOKEN_KEY)`）。

- 按事件分发回调（`onWS(event, fn)`）。

- 断线后 3 秒自动重连。

> 注意：小程序 WebSocket 的 Header 不能带自定义头，token 走首条消息鉴权。

### 6.2 连接生命周期（`src/App.vue`）

- 登录后 `connectWS()`，登出断开。

### 6.3 页面订阅刷新

| 页面                 | 订阅事件              | 回调             |
| ------------------ | ----------------- | -------------- |
| `order-detail.vue` | `order_changed`   | `reload`       |
| `orders.vue`       | `order_changed`   | `reload`       |
| `index.vue`        | `catalog_changed` | `loadData`     |
| `products.vue`     | `catalog_changed` | `loadProducts` |

***

## 7. 改动清单汇总

| 层   | 新增文件                                | 修改文件                                                                                             |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------ |
| 后端  | `app/core/ws.py`、`app/api/v1/ws.py` | `router.py`、`order/service.py`、`order/tasks.py`、`admin/service.py`、`after_sale/service.py`       |
| 后台  | `src/utils/ws.js`                   | `layout/Index.vue`、`Dashboard/Orders/AfterSales/Products/Categories/Banners/Coupons/Configs.vue` |
| 小程序 | `src/api/ws.js`                     | `App.vue`、`order-detail.vue`、`orders.vue`、`index.vue`、`products.vue`                             |

**不修改**：所有读接口、数据库结构、登录鉴权、支付集成、业务规则、页面模板/样式、`Members.vue`/`Admins.vue`、小程序其余 9 个页面。

***

## 8. 非功能需求

| 项       | 要求                                                                   |
| ------- | -------------------------------------------------------------------- |
| 断线重连    | 两端 3 秒自动重连                                                           |
| 推送不阻塞业务 | `notify` 异步提交，不阻塞写事务                                                 |
| 主题隔离    | 会员只能收到自己的订单推送（`order:{user_id}`），后台只能收到运营推送（`admin`），`public` 只推运营数据 |
| 鉴权      | 复用现有 token，登录逻辑不动                                                    |
| 兼容性     | 后台 WebSocket 复用 `/admin` 代理；小程序生产需 `wss://` + 备案域名                   |

***

## 9. 已确认决策

| 决策点        | 结论                                                   |
| ---------- | ---------------------------------------------------- |
| 鉴权方式       | 复用现有 token（后台 `admin_token`、小程序 `mall-token`），登录逻辑不动 |
| 断线重连       | 两端 3 秒自动重连                                           |
| 小程序首页/商品列表 | 订阅 `catalog_changed`，后台改运营数据后自动刷新                    |
| 推送粒度       | 只发事件信号，前端重新拉取                                        |
| 订阅消息       | 本期不做，二期再做                                            |

