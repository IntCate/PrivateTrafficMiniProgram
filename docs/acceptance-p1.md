# 快乐购商城 - P1 二期验收报告

> 验收时间：2026-09-05　|　范围：PRD §6.2 P1 二期（售后工单、优惠券、积分、管理后台、订单超时关闭；微信支付真实接入除外）
> 验收口径：PRD §6.3 —— 以接口文档用例为准，核心用例（售后状态机流转、后台售后再审核、券/积分核销、后台 RBAC、超时关单）必须覆盖并有通过记录。
> 参照基准：`docs/api-design.md`（契约，§11 coupon/points、§12 售后、§13 管理后台）、`docs/test-cases.md`（B5-14 / B8 / B9）、`docs/known-issues.md`（技术债）。
> 通用验收流程：①范围锁定 → ②质量门禁 → ③功能核对 → ④契约一致性 → ⑤复现证据 → ⑥结论与遗留（详见 §0）。

***

## 0. 通用验收流程（供后续 P2/上线复用于本仓库）

```
① 范围锁定  →  ② 质量门禁  →  ③ 功能核对  →  ④ 契约一致性  →  ⑤ 复现证据  →  ⑥ 结论与遗留
  PRD§6        pytest/ruff/mypy   service/api/前端逐用例    文档=后端=前端  可复跑命令/库      通过/待办
```

| 阶段      | 动作                | 依据                      | 本仓库证据输出                    |
| ------- | ----------------- | ----------------------- | -------------------------- |
| ① 范围锁定  | 列验收对象，核对"交付=文档口径" | PRD §6 / api-design §14 | 验收对象清单                     |
| ② 质量门禁  | 自动化测试 + 静态检查全绿    | test-cases B 部分         | `pytest` / `ruff` / `mypy` |
| ③ 功能核对  | 逐模块逐用例核对实现与预期     | test-cases B5-14/B8/B9  | service/api/页面引用           |
| ④ 契约一致性 | 三方对齐              | api-design              | schema ↔ ORM ↔ `.vue`      |
| ⑤ 复现证据  | 保留可复跑验收命令/库       | environment.md          | `mall_*_test` 库 + 命令       |
| ⑥ 结论与遗留 | 判定通过与待办           | known-issues            | 遗留清单                       |

***

## 1. 验收结论

**P1 二期通过验收（除微信支付真实接入外）。** 四大块全部实现并通过全量单测 + 真实 MySQL 集成测试：售后工单（申请/列表/详情/后台审核/订单状态联动）、优惠券 + 积分（领取/列表/抵扣/流水）、管理后台（登录 + JWT/RBAC + 商品/分类/订单/售后/会员/运营位/券/数据概览/配置 12 页面）、订单超时关闭定时任务（1405）。代码质量门禁（pytest 250 / ruff / mypy 92 files）全绿；`known-issues.md` #10/#11 本轮全部修复，#9 头像白名单部分解决。

遗留项为「微信支付真实接入（#7）」与「敏感词过滤（#9 ②）」，后者为 P2 合规增强、前者依赖外部商户资质，均不阻塞 P1 验收，见 §6。

***

## 2. 验收环境

| 项    | 值                                                                                                       |
| ---- | ------------------------------------------------------------------------------------------------------- |
| 后端   | FastAPI + SQLAlchemy 2.x + Alembic（`mall-backend/`），`.venv`                                             |
| 数据库  | MySQL 8，`127.0.0.1:3306`（用户 test）                                                                       |
| 验收库  | `mall_admin_test`（API 集成测试专用，schema 由 conftest drop/recreate，不污染开发库 `mall`）                             |
| 前端   | 小程序 uni-app Vue3（`mall-miniapp-uni/`）；后台 Vue3/Vite（`mall-admin/`，12 页面）                                 |
| 定时任务 | `core/scheduler.py`（BackgroundScheduler + IntervalTrigger）→ `order/tasks.py` `close_timeout_orders_job` |

***

## 3. 验收结果总表

| #  | 验收项        | 结果   | 明细                                                                     |
| -- | ---------- | ---- | ---------------------------------------------------------------------- |
| 1  | 后端全量单测     | ✅ 通过 | pytest `tests/`：**250 passed**                                         |
| 2  | P1 相关用例    | ✅ 通过 | 售后 21 / 券+积分 11 / 后台 115 = **147 passed**（精确匹配 test-cases 声称）          |
| 3  | 代码规范（ruff） | ✅ 通过 | `ruff check app tests`：All checks passed                               |
| 4  | 类型检查（mypy） | ✅ 通过 | `mypy app`：92 source files，0 issues                                    |
| 5  | 售后工单功能     | ✅ 通过 | B5-14a\~d 全覆盖（见 §4.1 + §5.1）                                           |
| 6  | 优惠券/积分功能   | ✅ 通过 | B8-1\~6 全覆盖（见 §4.2）                                                    |
| 7  | 管理后台功能     | ✅ 通过 | B9-1\~9：登录/RBAC/商品/分类/订单/售后/会员/运营位/券/概览/配置（见 §4.3）                     |
| 8  | 订单超时关闭     | ✅ 通过 | 1405：`close_timeout_orders` 关单 + 回补 lock\_stock，幂等（见 §4.4）             |
| 9  | 契约三方一致     | ✅ 通过 | 售后 images/statusText、结算、address、list 别名 = 文档=后端=前端（见 §5.2）             |
| 10 | 文档-代码一致    | ✅ 通过 | known-issues #8（1405）/ #10（1004）/ #11（fastapi）已解决，#9 ①头像白名单已解决（见 §5.3） |

***

## 4. 执行明细

### 4.1 售后工单功能（B5-14a\~d，端到端 + 单测）

- 申请：合法/订单不存在/非本人/状态非法/重复申请/原因必填/类型非法 → 成功生成 applying（amount=实付金额，`refund_type` 跟随 `type`）；`404`/`1403`/`1402`/`1606` ✓

- 列表/详情：按 status 筛选 + 分页，statusText 正确；详情 `404`/`1403` ✓

- 订单状态联动：申请后详情/列表 `statusText=申请中`、`statusDesc=退款申请已提交…`；后台审核通过后自动变 `已通过`/`退款申请已通过…`（`_apply_after_sale_progress` 动态覆盖，列表 `_after_sale_text_by_order` 与详情口径一致）✓

- 角标与排序：`orderStats.refund` 只计"申请中"=1；refund tab 客户端把"申请中"排前 ✓

- 凭证上传：`POST /api/upload` category=after\_sale/avatar 落库 `images`，后台 `AfterSales.vue` 用 `el-image` 预览（非 8 集成断言含 category 白名单校验）✓

- 后台审核：`audit_after_sale` 仅 applying 可审，非 applying `1607`；通过→approved / 驳回→rejected + `audit_remark` ✓

### 4.2 优惠券 / 积分（B8）

- 领取：合法 / 重复（`1602`）/ 不存在（`1601`）/ 停用/过期/未生效/已领完（`1603`）；成功后 `received_count+1` 生成 unused 用户券 ✓

- 列表：按 status 筛选 + 分页，`couponCount` 统计未使用券数 ✓

- 下单用积分：`pointsUsed` 抵扣正确 + 写 consume 流水；不足 `1605` ✓

- 确认收货得分：shipped → completed 积分增加 + 写 earn 流水（按实付金额取整）✓

### 4.3 管理后台（B9-1\~9，57 条真实 MySQL 集成 + 58 条 service）

- 登录 / 管理员管理：正确返回 JWT；密码错/禁用/不存在 `1701`；创建重名 `1702`；禁用自己 `1703`；RBAC 仅 admin ✓

- 商品/分类：CRUD、上下架、删除（软删）、SKU 维护、分类不存在 404；admin+operator 可访问 ✓

- 订单：列表/详情/发货，非 paid 发货 `1402`；finance 可查不可发 ✓

- 会员：列表/禁用/启用，不存在 404；禁用仅 admin（`update_member_status`）✓

- 运营位/优惠券：CRUD/券模板/发放，券/会员不存在 404 ✓

- 售后审核 / 数据概览 / 配置：通过/驳回/非 applying `1607`；概览统计、配置仅 admin ✓

- 前端页面：`mall-admin` 12 页面（Login/layout + AfterSales/Members/Coupons/Orders/Products/Categories/Banners/Admins/Dashboard/Configs）齐备 ✓

### 4.4 订单超时关闭（1405）

- `close_timeout_orders`：扫描 `pending` 且超时阈值前的订单 → 置 cancelled + `cancel_reason="订单超时未支付，系统自动关闭"` + 回补 lock\_stock（`_release_stock`）；仅处理 pending，幂等 ✓

- 调度接入：`init_scheduler` → `BackgroundScheduler` 间隔触发 `close_timeout_orders_job`（lifespan 启动），与 #11 on\_event→lifespan 迁移一并验证 ✓

***

## 5. 一致性核对

### 5.1 接口清单（P1 新增，均已在 api-design §11/§12/§13 落地）

| 模块  | 接口                                                                         | 实现                              |
| --- | -------------------------------------------------------------------------- | ------------------------------- |
| 售后  | `POST /api/after-sales`、`GET /api/after-sales`、`GET /api/after-sales/{id}` | after\_sale/api.py + service.py |
| 上传  | `POST /api/upload`（category=after\_sale/avatar）                            | common/api.py + upload.py       |
| 优惠券 | `GET /api/coupons`、`POST /api/coupons/{id}/receive`                        | coupon 模块                       |
| 积分  | `GET /api/points-logs`                                                     | points 模块                       |
| 后台  | login + 商品/分类/订单/售后/会员/运营位/券/概览/配置                                         | admin/api.py + service.py       |

### 5.2 关键契约三方一致（文档=后端=前端）

- 后台售后：`AfterSaleAdminItemOut` 返回 `images`（`field_validator` 归一 NULL），`AfterSales.vue` 用 `el-image` 预览 —— api-design §12.2 ✓

- 售后 statusText/statusDesc 动态覆盖：列表（`_after_sale_text_by_order`）与详情（`_apply_after_sale_progress`）口径一致 —— api-design §9.3/§9.4 = order/service.py = orders.vue/order-detail.vue ✓

- `statusText` 映射 applying/approved/rejected/refunded/closed —— `AFTER_SALE_STATUS_TEXT` = api-design §12.2 ✓

- 列表别名字段 `list` 别名序列化 —— `CamelModel` + `serialization_alias`（#11 修复后正常输出） ✓

### 5.3 技术债处理（known-issues，本轮 P1 涉及）

| #  | 问题                         | 处理                                                      |
| -- | -------------------------- | ------------------------------------------------------- |
| 8  | 1405 订单超时未支付未实现            | ✅ `close_timeout_orders` + scheduler 落地（1404/1406 仍 P2） |
| 9  | 会员资料校验                     | ✅ ①头像 `/uploads/` 白名单已收紧；②敏感词过滤待接入（P2）                  |
| 10 | 禁用会员登录语义过载                 | ✅ 登录用独立码 `1004`，api-design §1.3/§16.3 同步                |
| 11 | Pydantic 告警 + on\_event 弃用 | ✅ 根因 fastapi 过旧，升级 0.141.1 后告警清零；on\_event 迁 lifespan   |

***

## 6. 遗留与待办（不阻塞 P1 验收）

| 项              | 说明                                                                       | 归属           |
| -------------- | ------------------------------------------------------------------------ | ------------ |
| #7 微信支付真实接入    | 依赖商户号 + API v3 密钥 + 回调域名；`PAY_MODE=wechat` 目前返回 payParams 不改状态（mock 不受阻） | P1 遗留 + 外部资质 |
| #9 ② 敏感词过滤     | 无词库；接入后命中昵称返回 `1003`                                                     | P2           |
| #8 ② 1404/1406 | 金额校验（当前服务端全算无比对入口）/ 并发锁库存（`SELECT FOR UPDATE`）                           | P2 上线前       |
| A 部分 H5 人工手测   | A01\~A28 需真实浏览器交互，自动化无法覆盖                                                | 前端手测         |
| 性能放量复核         | 本机冒烟 avg<10ms，上线前压测 + 索引命中确认                                             | 上线前          |

***

## 7. 复现指引

```bash
# 后端质量门禁（API 集成需本机 MySQL 8，自动用 mall_admin_test 库，不污染 mall）
cd mall-backend
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m mypy app
# P1 相关用例单独复跑
.\.venv\Scripts\python.exe -m pytest tests/unit/test_after_sale.py tests/unit/test_coupon.py tests/unit/test_points.py tests/unit/test_admin.py tests/api/test_admin_api.py tests/api/test_after_sale_api.py -q
```

> 注：API 集成测试（`tests/api/*`）经 `tests/api/conftest.py` 使用独立库 `mall_admin_test`（session 级建表、逐测试清空重插种子，含三管理员 admin/operator/finance + 三角色 RBAC），证据可复跑。

