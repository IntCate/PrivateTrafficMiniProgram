# 快乐购商城 - P0 一期验收报告

> 验收时间：2026-09-02（首验）｜2026-09-04（复验 ×2）　|　范围：PRD §6.1 P0（微信登录 mock → 首页/分类/商品 → 购物车 → 地址 → 订单（支付 mock）→ 收藏 → 会员中心）
> 验收口径：PRD §6.3 —— 以接口文档用例为准，核心用例（加购幂等、下单锁库存、取消回补、并发下单、默认地址唯一、订单状态机非法流转）必须覆盖并有通过记录。
> 参照基准：`docs/api-design.md`（契约）、`docs/test-cases.md`（B 部分后端用例）、`docs/known-issues.md`（技术债）。
> 复验说明（2026-09-04）：前端购物车/商品详情/地址编辑 3 页 UI 改动（数量折叠徽章、步进器紧凑化、地址编辑样式）后，重新执行全量验收——pytest 94 / ruff / mypy 全绿、mall_accept 重建+种子导入、E2E 主链路 24/24、H5 生产构建均通过；期间发现 docs/ 被外部编辑器覆盖（known-issues 状态回退 + 4 个文档格式重排），已按 `git checkout --` 恢复权威版本，并将前端折叠数量交互同步进 test-cases A11/A27。

***

## 1. 验收结论

**P0 一期通过验收。** 后端 35 个 C 端接口全部实现并通过全量单测 + 真实 MySQL 主链路 E2E；前端 12 页面已全部切后端数据并可生产构建；数据库可从零迁移建库并导入种子；代码质量门禁（pytest/ruff/mypy）全绿；文档与代码三方（契约/后端/前端）一致；`known-issues.md` #1~#6 技术债本轮全部修复。

遗留项为「A 部分 H5 人工手测（A01~A28）」「微信真实资质（登录/支付）」与「后台（P1）」——均不阻塞 P0 验收，见 §6。

***

## 2. 验收环境

| 项 | 值 |
| --- | --- |
| 后端 | FastAPI + SQLAlchemy 2.x + Alembic（`mall-backend/`） |
| 数据库 | MySQL 8，`127.0.0.1:3306`（用户 test） |
| 验收库 | `mall_accept`（从零 Alembic 迁移建库 + 导入前台种子，不污染正式 `mall`） |
| 前端 | uni-app Vue3（`mall-miniapp-uni/`），H5 生产构建 `npm run build:h5` |
| 运行时 | Python `.venv`（mall-backend） |

***

## 3. 验收结果总表

| # | 验收项 | 结果 | 明细 |
| --- | --- | --- | --- |
| 1 | 后端全量单测 | ✅ 通过 | pytest `tests/`：**94 passed**（auth/member/product/cart/address/order/favorite/utils/health） |
| 2 | 代码规范（ruff） | ✅ 通过 | `ruff check app tests`：All checks passed |
| 3 | 类型检查（mypy） | ✅ 通过 | `mypy app`：73 source files，0 issues（可作 CI 门禁） |
| 4 | 数据库从零建库 | ✅ 通过 | `mall_accept` 执行 7 个 Alembic 迁移版本 → 12 表（10 业务表 + `member_session` + `alembic_version`） |
| 5 | 种子数据导入 | ✅ 通过 | category=5、product=10、product_sku=32、banner=7；会员/购物车/地址/订单/收藏空表（由用户操作产生） |
| 6 | 主链路 E2E | ✅ 通过 | 真实 MySQL `mall_accept`，TestClient 全栈：**24/24 断言通过**（见 §4.1） |
| 7 | 前端生产构建 | ✅ 通过 | `npm run build:h5` → DONE Build complete（仅 Sass legacy-js-api 弃用告警，无阻塞） |
| 8 | 性能冒烟 | ✅ 通过 | 热点接口 avg 7.1~9.1ms（n=20，见 §4.2） |
| 9 | 接口清单核对 | ✅ 通过 | 后端 35 个 C 端业务路由 = api-design 模块总览 §2（见 §5.1） |
| 10 | 契约三方一致 | ✅ 通过 | 结算预览/下单/地址/商品列表字段 文档=后端=前端（见 §5.2） |
| 11 | 文档-代码一致 | ✅ 通过 | schema.sql 与 ORM/迁移三端一致；known-issues #1~#6 已解决（见 §5.3） |

***

## 4. 执行明细

### 4.1 主链路 E2E（24 项断言全通过）

```
登录 → 首页聚合(会员) → 分类列表(5) → 商品列表(下架过滤 total=9)
→ 商品详情(skus=2) → 加购(勾选) → 购物车列表 → 结算预览(pay=89.0)
→ 新增地址(默认) → 创建订单(pending) → 库存预占(88→87)
→ 支付成功(paid) → 订单详情(availableActions=[remind,refund,buyAgain])
→ 第二单取消(cancelled) → 取消回补库存(85→86)
→ 售后退款(refund) → 退款回补实扣(87→87)
→ 收藏幂等(existed=true) → 收藏列表(1) → 会员概览(stats.refund=1)
→ 资料更新合法/非法(1003) → 退出登录(loggedOut) → 未登录 401
```

覆盖口径：加购幂等（B3-3）、下单锁库存（B5-4）、取消回补（B5-7）、售后退款回补（B5-14）、支付实扣+重复支付拦截（B5-6）、默认地址唯一（B4-4/首条默认）、状态机非法流转 1402（B5-10，联调日志验证第二次取消返回 1402）、越权/未登录 401（B1-4）。

### 4.2 性能冒烟（n=20，单位 ms）

| 接口 | avg | max | status |
| --- | --- | --- | --- |
| 首页聚合 `GET /api/home/index` | 9.1 | 10.5 | 200 |
| 商品列表 `GET /api/products` | 7.6 | 8.2 | 200 |
| 商品详情 `GET /api/products/{id}` | 7.1 | 9.6 | 200 |
| 购物车列表 `GET /api/cart` | 7.7 | 8.5 | 200 |

本机冒烟（含鉴权/序列化/日志），无索引命中瓶颈；P1 上线前建议压测放量后复核。

### 4.3 数据库迁移链验证

从零执行 `alembic upgrade head`（7 个版本：init member/session → category/product/sku/banner → shipping_address → cart → orders/order_item → favorite → 字段对齐）→ 表结构核对通过；随后导入 `docs/sql/seed-data.sql`（前台段）成功。

***

## 5. 一致性核对

### 5.1 接口清单（后端 35 路由 = 文档 §2 模块总览）

| 模块 | 接口数 | 明细 |
| --- | --- | --- |
| 认证 | 2 | login、logout |
| 会员 | 2 | overview、PUT profile |
| 首页 | 1 | home/index |
| 分类 | 1 | categories |
| 商品 | 2 | products 列表、products/{id} 详情 |
| 购物车 | 6 | 列表、加购、改数量/勾选、删单/批量、select-all |
| 地址 | 5 | 列表、新增、改、删、设默认 |
| 订单 | 13 | preview、preview-direct、direct、创建、stats、列表、详情、pay、cancel、refund、remind、confirm、buy-again |
| 收藏 | 3 | 列表、加、删 |

售后 / 优惠券 / 积分 / 管理后台为骨架占位（P1），与文档「预留」一致。

### 5.2 关键契约三方一致（文档=后端=前端）

- 结算预览：`GET /api/orders/preview?cartItemIds=`，返回 `totalAmount/freight/payAmount/addresses`，商品项带 `cartItemId` —— api-design §9.1 = order/schemas.py = order-confirm.vue ✓
- 创建订单：`POST /api/orders {addressId, items:[{skuId,quantity}]}` —— api-design §9.2 = CreateOrderRequest = order-confirm.vue ✓
- 直购：`preview-direct`/`direct` 不写/不删购物车 —— api-design §9.1 = order/api.py = product-detail.vue ✓
- 地址：字段 `name/phone/province/city/district/detail`，返回带 `regionText` —— api-design §8 = address/schemas.py = address-edit.vue ✓
- 商品列表：不含 `skus`，下架项不进列表（total=9） —— api-design §6 = product/service.py = products.vue ✓

### 5.3 技术债处理（known-issues #1~#6 全部 ✅ 已解决）

| # | 问题 | 处理 |
| --- | --- | --- |
| 1 | 购物车规格弹层库存口径不一致 | 商品详情 `sku.stock` 改可用库存（`stock-lock_stock`），前端弹层与后端校验对齐 |
| 2 | ORM/迁移/schema 的 `deleted` 列三端不一致 | schema.sql 补 6 表 `deleted` 列、database-design §1.3 同步，三端一致 |
| 3 | member_session 过期会话无清理 | auth/service.py 登录时顺带清理该会员过期会话 |
| 4 | mypy 基线 7 处类型错误 | 7 处标注已修，`mypy app/` 全绿（73 files 0 issues） |
| 5 | seed-data.sql 后台段导致导入中断 | 拆前台段 `seed-data.sql` + 后台段 `seed-backend.sql` |
| 6 | mock 层未同步支付实扣/退款回补 | store.js 同步锁库存/实扣/回补口径 |

***

## 6. 遗留与待办（不阻塞 P0 验收）

| 项 | 说明 | 归属 |
| --- | --- | --- |
| A 部分 H5 人工手测（A01~A28） | 需真实浏览器交互（空态/步进器不冒泡/失效项置灰等 UI 行为），自动化无法覆盖 | 前端手测 |
| 微信真实登录/支付 | 依赖 appId/商户号资质，开发期 mock 不受阻 | P1 + 外部资质 |
| 订单超时关闭定时任务 | 见 `core/scheduler.py` 骨架，P1 落地 | P1 |
| 管理后台 | `/admin/api/*` 骨架占位，功能待 P1 定义 | P1 |
| 性能放量复核 | 本机冒烟 avg<10ms，上线前压测复核 + 索引命中确认 | P2 上线前 |

## 7. 复现指引

```bash
# 建验收库（不污染 mall）
mysql -utest -p123456 -e "CREATE DATABASE mall_accept CHARACTER SET utf8mb4"
# 后端回归
cd mall-backend && .\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m mypy app
# 前端生产构建
cd mall-miniapp-uni && npm run build:h5
```

> 注：验收库 `mall_accept` 保留作证据；正式环境仍用 `mall`（见 `.env`）。
