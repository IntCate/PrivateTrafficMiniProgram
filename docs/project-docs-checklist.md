# 快乐购商城 - 项目开发文档清单分析

> 本文档分析"快乐购（自营私域商城小程序）"当前文档与代码现状，维护开发前必备文档的产出状态与优先级，并列出后续待补充项。

---

## 1. 现状盘点

### 1.1 仓库现状

| 目录/文件 | 定位 | 状态 |
| --- | --- | --- |
| `mall-miniapp-uni/` | uni-app 小程序（Vue3 + Vite + SCSS），12 个页面 | 前端已实现（数据本地 mock） |
| `mall-miniapp-uni/README.md` | 项目说明 | 已补全：目录结构、页面说明、接口契约指引 |
| `docs/` | 项目文档目录 | 本文档所在目录 |

### 1.2 已具备的文档

- ✅ `docs/api-design.md` — API 接口设计文档（C 端 + 后台规划）
- ✅ `docs/database-design.md` — 数据库设计文档（17 张表）
- ✅ `docs/architecture.md` — 后端技术选型与架构设计（含可复用模板骨架，P0）
- ✅ `docs/prd.md` — 产品需求文档（P0）
- ✅ `docs/conventions/error-code.md` — 通用规范：错误码（P0）
- ✅ `docs/conventions/auth.md` — 通用规范：鉴权（P0）
- ✅ `docs/conventions/logging.md` — 通用规范：日志（P0）
- ✅ `docs/conventions/environment.md` — 通用规范：环境与接口联调（P0）
- ✅ `mall-miniapp-uni/README.md` — 跑通前端的技术说明（npm 命令等）

### 1.3 关键决策与外部依赖

| 项 | 状态与依据 |
| --- | --- |
| 后端技术栈与目录结构 | ✅ 已定：Python 3.11+ / FastAPI / SQLAlchemy / MySQL 8（首版无 Redis），见 `docs/architecture.md` |
| 认证方式 | ✅ 已定：C 端 token（`member_session` 表）+ 后台 JWT/RBAC，见 `docs/conventions/auth.md` |
| 错误码统一规范 | ✅ 已定：模块分段式，见 `docs/conventions/error-code.md` |
| 环境/域名/联调 | ✅ 已定：dev/test/prod 三层 + mock 策略，见 `docs/conventions/environment.md` |
| ✅ 业务范围 | 已定：首期 C 端 P0 全部实现 + 后台接口规划（P1 起） |
| ✅ `PAY_MODE` | 已定：首版 `mock` 先行，`wechat` 通道预留（需商户号） |
| ✅ 下单后购物车与取消订单可见性 | 已定：下单成功删除对应购物车项；取消订单以 `cancelled` 状态展示 |
| ✅ 购物车失效项展示（下架/库存为 0） | 已定：下架商品从列表/详情消失（1102），但购物车保留历史项并标记失效——DTO 携带 `onSale:false`，页面置灰 + 「已下架」角标 + 勾选锁定 + 数量控件隐藏，不参与金额合计；勾选失效项结算按 1203 拦截，取消勾选即剔除；全选只勾可售项，取消全选清空全部。见 `docs/api-design.md` §7.1 / §7.6 |
| ⚠️ 微信小程序 appid / 商户号资质 | 外部依赖：开发期 mock 不受阻；资质到位后切换真实登录/支付 |

---

## 2. 文档产出与后续计划

### 2.1 第一梯队：开工前必补（P0）—— 已完成 ✅

| # | 文档 | 交付物 | 备注 |
| --- | --- | --- | --- |
| 1 | **后端技术选型与架构设计文档** | ✅ `docs/architecture.md` | 含可复用模板设计：core/common 通用层 + modules 可插拔业务模块 |
| 2 | **产品需求文档（PRD）** | ✅ `docs/prd.md` | 业务规则基线（订单状态机/库存/默认地址/金额） |
| 3 | **接口联调与环境管理规范** | ✅ `docs/conventions/environment.md` | 三层环境、Base URL、CORS、mock 开关、微信资质前置 |
| 4 | **通用规范文档** | ✅ `docs/conventions/error-code.md` / `auth.md` / `logging.md` | 错误码分段、双体系鉴权、JSON 日志与脱敏 |

### 2.2 第二梯队：联调与开发期补（P1）

| # | 文档 | 原因 | 建议内容 |
| --- | --- | --- | --- |
| 5 | **微信登录 / 支付对接文档** | 依赖微信开放能力，需准备 appId/appSecret、商户号、回调配置 | 登录 code2session 流程、支付下单与回调验签流程、退款流程、沙箱/仿真说明、失败与边界处理 |
| 6 | **数据库初始化与迁移文档（SQL 脚本 + 说明）** | 数据库设计是大纲，落地需要可执行脚本与演进机制 | 建库建表 SQL、种子数据（分类/商品/SKU/运营位）、Alembic 方案、索引维护 |
| 7 | **后端代码规范**（并入架构文档或独立） | 多人协作与后续维护需要 | 命名、分层依赖规则、统一异常处理、事务边界、乐观锁/行锁使用约定 |
| 8 | **测试方案与用例文档** | 电商核心链路（下单-支付-发货）必须覆盖 | ✅ 已产出 `docs/test-cases.md`（A 部分 H5 手测 28 条 + B 部分后端接口用例，与 api-design 错误码/mock 对齐）；待补 Postman/Apifox 集合文件与压测要点 |
| 9 | **管理后台需求文档** | API 已规划后台接口，但功能与权限未定义 | 后台页面清单、功能说明、角色权限矩阵（admin/operator/finance，已列入 auth.md） |
| 10 | **数据字典 / 字典维护规范** | 状态码、分类、标签等枚举需前后端一致 | 枚举清单、扩展机制、前后端映射表 |

### 2.3 第三梯队：上线与运维配套（P2）

| # | 文档 | 原因 | 建议内容 |
| --- | --- | --- | --- |
| 11 | **部署架构与运维手册** | 保障可交付可运行 | 服务器规划（nginx/应用/DB）、Docker 编排或云服务器部署、备份与恢复、监控告警（日志、接口耗时、订单异常）、定时任务（订单超时关闭、库存回补） |
| 12 | **安全与合规清单** | 小程序涉及用户数据与支付 | HTTPS 强制、密钥管理、手机号/地址脱敏、隐私协议、支付安全、Web 漏洞自查（注入/XSS/越权 403） |
| 13 | **上线验收 Checklist** | 收尾把关，避免上线事故 | 功能验收（对照 PRD）、性能抽查、安全抽查、数据核对（订单金额对账）、回滚预案 |
| 14 | **版本规划与迭代计划** | API 文档第 14 节已列 P0/P1，需固化为排期 | 里程碑、迭代清单、依赖关系（如微信支付资质依赖） |

### 2.4 团队协作类（建议）

| # | 文档 | 原因 |
| --- | --- | --- |
| 15 | **Git 分支与提交规范** | `docs/` 目录已建立，仓库无统一提交约定 |
| 16 | **前端接入后端改造清单** | 前端本地 mock 需切后端，逐项改造点已列于 API 文档第 15 节（9 处必修项 + 依赖说明），可据此生成改造任务清单防止遗漏 |

---

## 3. 最小闭环建议（下一步）

1. ✅ **P0 文档已补齐**：架构/PRD/环境/通用规范，可按 `docs/architecture.md` 建立工程骨架
2. ✅ **文档颗粒度对齐（2026-09-01 精修轮）**：补齐结算预览/会员资料接口与售后模块；统一购物车上限、错误码兜底、会话清理、逻辑删除、等级字典等口径；补充购物车失效项展示口径（`onSale` 字段 + 结算 1203 拦截 + 全选语义，见 `api-design.md` §7.1/§7.6）
3. ✅ **测试方案与用例文档已产出**：`docs/test-cases.md`（A 部分 H5 手测 28 条 + B 部分后端接口用例），后端据此实现并回归
4. **建立后端工程骨架**：按 architecture.md 目录结构生成 `mall-backend/`，落地 core/common 模板层 + auth/member/product/cart/address/order/favorite/after_sale 模块空壳
5. **生成数据库脚本**：根据 `docs/database-design.md` 产出 `docs/sql/schema.sql` + `seed-data.sql`（17 张表 + 10 条商品等种子数据）
6. **跟踪外部资质**：微信 appid / 商户号（开发期 mock 不受阻；其余决策已在文档定稿，前端按文档契约实现）
7. **产出联调交付物**：Postman/Apifox 集合文件，与 `docs/api-design.md` 及 `docs/test-cases.md` B 部分配套

### 3.1 后端开发（P0 开工）前置 Checklist

> 下列项在编写后端接口代码**之前**应就绪；标 ✅ 的已完成，未标为待办。

| # | 前置项 | 状态 | 产出/说明 |
| --- | --- | --- | --- |
| 1 | 接口契约定稿 | ✅ | `docs/api-design.md`（§1~§16，含错误码、失效项展示、全选语义、错误码实测路径） |
| 2 | 错误码体系 | ✅ | `docs/conventions/error-code.md`（通用码 + 模块分段码，1102/1104/1201/1203/1301/1402/1403/1404/1405/1406 等） |
| 3 | 数据库设计 | ✅ | `docs/database-design.md`（17 张表，依赖路径已更新为 `src/api/mock/store.js`） |
| 4 | 前端 mock 核对结论 | ✅ | `docs/api-design.md` §16（契约核对记录 + 留给后端的实现提示） |
| 5 | 测试用例基线 | ✅ | `docs/test-cases.md`（B 部分为后端接口用例，后端落地后逐条回归） |
| 6 | 架构/工程骨架 | ⏳ | `docs/architecture.md` 已定；待生成 `mall-backend/` 骨架 |
| 7 | 数据库脚本 | ⏳ | 待产出 `docs/sql/schema.sql` + `seed-data.sql` + Alembic 方案 |
| 8 | 后端代码规范 | ⏳ | 待并入架构或独立（命名/分层/异常/事务/锁约定） |
| 9 | 联调工具集合 | ⏳ | 待产出 Postman/Apifox 集合（对齐 api-design + test-cases） |
| 10 | 外部资质 | ⚠️ | 微信 appid/商户号；开发期 mock 与测试小程序不受阻 |

> 建议开工顺序：6 骨架 → 7 脚本 → 8 规范 → 9 集合 → 各模块按 api-design §14 P0 清单实现，并对照 `test-cases.md` B 部分逐条回归。

---

## 4. 文档目录规划

```text
shopping/
├── docs/                               # 项目文档根目录
│   ├── api-design.md                   # ✅ API 接口设计文档
│   ├── database-design.md              # ✅ 数据库设计文档
│   ├── project-docs-checklist.md       # ✅ 本文档（文档清单分析）
│   ├── architecture.md                 # ✅ P0-1 技术选型与架构设计（模板化）
│   ├── prd.md                          # ✅ P0-2 产品需求文档
│   ├── test-cases.md                   # ✅ 测试用例文档（A: H5 手测 28 条 + B: 后端接口用例 + C: 一致性）
│   ├── conventions/                    # ✅ P0-4 通用规范
│   │   ├── error-code.md               # ✅ 错误码
│   │   ├── auth.md                     # ✅ 鉴权
│   │   ├── logging.md                  # ✅ 日志
│   │   └── environment.md              # ✅ 环境与联调
│   ├── integrations/
│   │   └── wechat.md                   # 🆕 P1-5 微信登录/支付
│   └── sql/                            # 🆕 P1-6 数据库脚本
│       ├── schema.sql
│       └── seed-data.sql
├── mall-backend/                       # 🆕 后端工程（按 architecture.md 骨架）
│   ├── app/（core/common/modules/integrations）
│   ├── alembic/
│   ├── tests/
│   └── .env.example
└── mall-miniapp-uni/                   # 前端（现有）
```