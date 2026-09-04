# 快乐购商城 - 后端技术选型与架构设计文档

> 项目：快乐购（自营私域商城小程序）
> 版本：v1.0
> 定位：本文档同时承担两类职责——①快乐购商城后端的落地骨架；②**可复用的通用后端模板**。新项目可基于本骨架快速拷贝生成，仅需调整配置与业务模块。

***

## 1. 技术选型

| 组件                | 版本     | 用途        | 选型理由                                              |
| ----------------- | ------ | --------- | ------------------------------------------------- |
| Python            | 3.11+  | 运行语言      | 生态成熟、类型提示完备，配合 FastAPI 开发效率高                      |
| FastAPI           | 0.110+ | Web 框架    | 异步高性能、自带 OpenAPI `/docs` 交互文档，RESTful + JSON 天然契合 |
| Uvicorn           | 0.29+  | ASGI 服务器  | 官方推荐，生产以 `nginx → uvicorn(多 worker)` 形态部署         |
| SQLAlchemy        | 2.0+   | ORM       | 声明式模型 + 会话管理；2.0 风格类型友好，易维护                       |
| PyMySQL           | 1.1+   | MySQL 驱动  | 纯 Python 驱动，部署零编译依赖                               |
| Alembic           | 1.13+  | 数据库迁移     | 结构演进可追踪、可回滚，替代人工手改 SQL                            |
| Pydantic          | 2.x    | 参数校验/序列化  | FastAPI 内置，请求出参一栈式声名与校验                           |
| pydantic-settings | 2.x    | 环境配置      | `.env` 驱动的分层配置                                    |
| PyJWT             | 2.8+   | 后台登录 JWT  | 无状态鉴权，管理端多实例友好                                    |
| passlib/bcrypt    | —      | 密码哈希      | 管理员密码 BCrypt 存储                                   |
| httpx             | 0.27+  | 出站 HTTP   | 调微信 `code2Session`、`getPhoneNumber` 等官方接口         |
| APScheduler       | 3.10+  | 定时任务      | 进程内调度订单超时关闭、库存回补（首版不依赖外部组件）                       |
| pytest            | 8.x    | 测试        | 分层测试（单元/接口）                                       |
| ruff / mypy       | —      | 静态检查/类型检查 | 统一代码质量                                            |

**明确不引入（首版）**：Redis（会话与缓存全部落 MySQL），MQ（无异步削峰诉求）。二者在架构上预留接入点，见 §5.6 与 §7。

***

## 2. 通用模板设计（核心原则）

本套骨架按"**一次搭建、处处复用**"设计，分为**通用核心层**与**可插拔业务模块层**。

### 2.1 分层定位

| 层                    | 职责                                    | 是否随业务变化    |
| -------------------- | ------------------------------------- | ---------- |
| `core/` 通用核心         | 配置加载、数据库会话、统一异常/响应、安全守卫、日志、调度器        | 不动，模板级     |
| `common/` 通用工具       | 分页、脱敏、订单号生成、上传抽象、通用依赖                 | 基本不动，可增量扩展 |
| `modules/` 业务模块      | 每个业务域一个包：auth/member/product/cart/... | 随项目增删，可插拔  |
| `integrations/` 三方对接 | 微信、支付（预留）等                            | 随项目增删      |

### 2.2 模板能力清单（新项目开箱即得）

- 统一响应结构 `{code, message, data}` 与统一分页对象（见 [error-code.md](conventions/error-code.md)）

- 统一业务异常 `BizException(code, message)` + 全局异常处理器（参数错误/未登录/无权限/资源不存在/服务器错误）

- 双体系鉴权：C 端会员 `token`（MySQL 会话表）+ 后台 `JWT + RBAC`（见 [auth.md](conventions/auth.md)）

- 通用模型基类：`BaseFields`（id/created\_at/updated\_at）+ 可选 `SoftDeleteMixin`（deleted 逻辑删除，按需继承）

- 通用仓储基类：`get / get_by / page / save / update / delete`，业务仓储继承即用

- 通用配置模块：`sys_config` 键值配置 + 后台热更新

- 请求日志中间件 + request\_id 链路追踪 + 敏感字段脱敏（见 [logging.md](conventions/logging.md)）

- 定时任务调度器（APScheduler），业务任务注册即用

- Alembic 迁移骨架、pytest 分层测试骨架、ruff/mypy 配置、`.env.example`

### 2.3 业务模块"四件套"规范

每个业务模块固定由 4 个文件组成（复杂模块可拆 `service.py` 为多文件）：

```text
modules/<biz>/
├── models.py       # SQLAlchemy 模型（继承 common Base）
├── schemas.py      # Pydantic 入/出参
├── repository.py   # 继承 BaseRepository 的数据访问
└── api.py          # APIRouter + service 编排（service 逻辑简单时可并入 api.py）

# 复杂业务（如 order）再增加：
└── service.py      # 事务编排：下单锁库存、金额计算等
```

新增业务步骤：拷贝模块骨架 → 建模型 → 写 schema → 写仓储 → 写路由 → 在 `api/router.py` 注册 → 生成 Alembic 迁移。**不修改 core/ 与 common/ 任何代码**。

### 2.4 模板复用方式

1. 拷贝骨架目录，重命名项目；
2. 修改 `.env`（数据库连接、密钥、微信 appid 等）与 `core/config.py` 的工程名/前缀；
3. 按需增删 `modules/` 下的业务模块与 `integrations/` 三方对接；
4. 需要缓存/队列时，仅替换 `common/` 中的存储实现为 Redis 方案，模块代码不改。

***

## 3. 项目目录结构

```text
mall-backend/
├── app/
│   ├── main.py                    # FastAPI 入口：中间件、路由注册、启动事件
│   ├── core/                      # ── 模板级通用核心 ──
│   │   ├── config.py              # pydantic-settings 分层配置
│   │   ├── database.py            # 引擎、会话工厂、get_db 依赖
│   │   ├── models.py              # Base、BaseFields、SoftDeleteMixin(软删按需)
│   │   ├── exceptions.py          # BizException 及全局异常处理器
│   │   ├── response.py            # 统一响应、PageResult
│   │   ├── security.py            # 密码哈希、token 生成/校验、鉴权守卫
│   │   ├── logging.py             # JSON 日志、request_id 中间件
│   │   └── scheduler.py           # APScheduler 初始化与注册
│   ├── common/                    # ── 模板级通用工具 ──
│   │   ├── deps.py                # get_db / get_current_member / require_roles / pagination
│   │   ├── enums.py               # 通用枚举
│   │   ├── utils.py               # 订单号、随机数、时间、脱敏
│   │   └── upload.py              # 上传抽象（本地磁盘，OSS 预留接口）
│   ├── modules/                   # ── 业务模块（可插拔）──
│   │   ├── auth/                  # 微信登录（code → openid → token）
│   │   ├── member/                # 会员中心、头像昵称、会员概况
│   │   ├── product/               # 分类、商品、SKU、搜索
│   │   ├── cart/                  # 购物车
│   │   ├── address/               # 收货地址
│   │   ├── order/                 # 订单、订单明细、支付(mock/微信)
│   │   ├── favorite/              # 收藏
│   │   ├── coupon/                # 优惠券（P1）
│   │   ├── points/                # 积分流水（P1）
│   │   └── admin/                 # 后台：登录、商品/订单/会员/运营位/配置管理
│   ├── integrations/              # ── 三方对接 ──
│   │   ├── wechat.py              # code2Session、getPhoneNumber
│   │   └── pay.py                 # 微信支付（P1 预留接口）
│   └── api/
│       └── v1/
│           ├── router.py          # 所有模块路由统一注册点
│           └── ...（模块路由在各 modules/*/api.py 内定义）
├── alembic/                       # 数据库迁移
│   ├── env.py
│   └── versions/
├── tests/                         # tests/unit、tests/api
├── scripts/                       # 初始化、备份脚本
├── .env.example                   # 环境变量模板
├── requirements.txt
└── README.md
```

***

## 4. 分层规范与依赖规则

### 4.1 调用方向（严禁反向/跨层）

```text
api.py(路由) → service.py(业务) → repository.py(数据) → models.py(ORM)
     │              │                  │
     └ schemas.py（出入参定义，仅出现在 api 边界）
```

- `api.py` 只做"收参 → 校验 → 调服务 → 统一返回"，不写 SQL；

- `service.py` 承载业务规则与事务边界（下单锁库存、金额计算、状态机流转）；

- `repository.py` 只做数据读写，不承载业务；

- **禁止**模块之间直接 import 对方的 `repository`，跨模块协作统一走对方 `service` 暴露的方法（如"下单"调"会员"积分/券的校验）。

### 4.2 通用约束

- 所有接口返回统一响应体（见 [error-code.md](conventions/error-code.md)）；只写 `data` 字段名，序列化由 pipe 完成；

- 分页统一 `page` / `pageSize`（默认 10，最大 50），统一返回 `PageResult`；

- 数据库字段一律下划线，API 字段一律驼峰，由 Pydantic `alias_generator` 自动转换，业务代码不手写映射；

- 写操作默认开事务：`service` 内用 `with db.begin()` 或仓储事务装饰器包裹，异常自动回滚；

- 禁止 `SELECT *`；列表查询必须走索引（`idx_user`、`uk_username` 等见数据库设计文档）；

- 金额用 `Decimal` 计算，入库 `DECIMAL(10,2)`，派发前端为字符串/数字前统一两位小数。

***

## 5. 通用能力设计

### 5.1 统一响应与分页

- 成功：`{ "code": 0, "message": "ok", "data": ... }`

- 失败：`{ "code": 400, "message": "参数错误", "data": null }`（错误码段见 [error-code.md](conventions/error-code.md)）

- 分页：`{ "list": [...], "total": 100, "page": 1, "pageSize": 10, "hasMore": false }`

### 5.2 统一异常

- 业务异常：`raise BizException(code, message)`，全局 handler 捕获后返回对应 HTTP 状态与业务码；

- 系统异常：未知异常经中间件兜底返回 `500`，同时写 error 日志，不向前端泄露堆栈。

### 5.3 鉴权

- C 端：`Authorization: Bearer {token}` → 查 `member_session` 表 → 注入 `current_member`；

- 后台：`Authorization: Bearer {jwt}` → 解码校验 → 注入 `current_admin`，配合 `require_roles("admin","operator")` 做 RBAC；

- 具体见 [auth.md](conventions/auth.md)。

### 5.4 配置中心

- 通用键值：`sys_config` 表，后台 `GET/PUT /admin/api/configs` 热更新；

- 全局配置由 `core/config.py` 负责；运营配置（客服电话、运费规则等）由 `sys_config` 负责，两级分工不混用。

### 5.5 日志与追踪

- 每个请求生成 `request_id`（响应头回传），贯穿访问日志与业务日志；

- 日志 JSON 化，含 `request_id / method / path / status / cost_ms / user_id / ip`；

- 手机号、token、openid、session\_key 一律脱敏（见 [logging.md](conventions/logging.md)）。

### 5.6 定时任务（APScheduler）

| 任务     | 周期     | 说明                                                        |
| ------ | ------ | --------------------------------------------------------- |
| 订单超时关闭 | 每 1 分钟 | `orders.status=pending` 且超 2 小时未支付 → 关闭 + 回补 `lock_stock` |
| 过期会话清理 | 每日     | 删除 `member_session.expires_at < NOW()` 的记录（惰性校验以外的兜底）     |

> 说明：上表为**业务任务示例**，模板层仅提供 APScheduler 调度器载体与统一注册入口（`scheduler.py`），具体任务由各业务模块在启动时按需注册。

> 预留：当需要跨实例锁定时，将任务切换为 Redis 分布式锁或外部调度器，`scheduler.py` 接口不变。

### 5.7 数据库会话与事务

- `get_db` 依赖：每个请求一个 Session，请求结束自动关闭；

- 事务边界在 `service` 层：下单/支付/取消等写多表操作整体包裹，任一失败整体回滚；

- 高并发写（库存、优惠券、积分）使用事务内 `SELECT ... FOR UPDATE` 行锁，见数据库设计 §6。

***

## 6. 业务模块落地（快乐购映射）

| 模块              | 主要职责                                  | 对应接口文档                    |
| --------------- | ------------------------------------- | ------------------------- |
| auth            | 微信静默登录、登出                             | api-design §3             |
| member          | 会员概况、资料更新、优惠券、积分                      | api-design §11            |
| product         | 首页聚合、分类、商品列表/详情/搜索、运营位                | api-design §4/§5/§6       |
| cart            | 加购/改量/勾选/删除/结算信息                      | api-design §7             |
| address         | 增删改查 + 默认地址                           | api-design §8             |
| order           | 结算预览、下单(锁库存)/支付(mock→wechat)/取消/收货/查询 | api-design §9             |
| favorite        | 收藏增删查                                 | api-design §10            |
| coupon / points | 券领取核销、积分流水（P1）                        | api-design §11.3/§11.4 预留 |
| after\_sale     | 申请售后、售后单查询（P1）                        | api-design §12 预留         |
| admin           | 后台全模块管理（P1）                           | api-design §13            |

***

## 7. 环境与配置管理

- 三层环境：`dev`（本地开发）/ `test`（联调验收）/ `prod`（生产），各自独立 `.env`；

- 配置项清单与 Base URL、CORS 规则见 [environment.md](conventions/environment.md)；

- 密钥类（`SECRET_KEY`、`WX_APP_SECRET`、`DB_PASSWORD`）只允许在 `.env`/密钥服务中配置，**禁止写入代码与文档**，`.env` 不进版本库。

***

## 8. 数据库迁移（Alembic）

- 每个业务模块的模型变更生成一条迁移脚本：`alembic revision --autogenerate -m "desc"`；

- 上线顺序：先执行迁移再发代码；回滚用 `alembic downgrade -1`；

- 严禁手工改库；生产变更必须走迁移脚本并备份。

***

## 9. 测试与质量

| 级别   | 覆盖                     | 工具                        |
| ---- | ---------------------- | ------------------------- |
| 单元测试 | service 规则、金额计算、状态机、脱敏 | pytest                    |
| 接口测试 | 鉴权、CRUD、分页、下单/取消回补链路   | pytest + httpx/TestClient |
| 静态检查 | ruff（导入/未用变量/命名）       | ruff                      |
| 类型检查 | 全量类型标注                 | mypy                      |

提交前强制通过 `ruff check . && mypy app && pytest`。

***

## 10. 上线形态

```text
用户 → HTTPS → nginx（80/443，反代 + 静态资源）→ uvicorn worker 集群 → MySQL 8
                                            └───────── APScheduler（主进程）
```

- 进程：`uvicorn app.main:app --workers N`（单机多 worker，写操作依赖 MySQL 行锁保证并发正确）；

- 微信接口调用（code2Session、支付回调验签）需要 HTTPS 公网域名，且微信后台配置服务器域名白名单；

- 定时任务首版跑在唯一主进程内；多实例时按 §5.6 预留方案收敛为单实例执行。

```
```

