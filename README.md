# 快乐购商城 · 自营私域商城（微信小程序）

> 面向普通消费者的自营 B2C 微信小程序商城，覆盖「逛 → 加购 → 下单 → 收货」完整购物链路，并包含收藏、优惠券、会员积分等运营能力。

| 项    | 说明                                           |
| ---- | -------------------------------------------- |
| 终端   | 微信小程序（uni-app / Vue3 / Vite），后端为 RESTful API |
| 商业模式 | 自营 B2C，微信支付收款（首版可用 mock 代付）                  |
| 一期范围 | C 端全链路 + 微信登录（mock 可用）                       |
| 二期范围 | 后台管理、微信支付真实接入、售后、优惠券、积分流水                    |

## 仓库结构

```
shopping/
├── docs/                     # 需求 / 架构 / 接口 / 数据库设计 / 测试用例 / 规范
├── mall-backend/             # 后端（FastAPI + MySQL）
├── mall-miniapp-uni/         # C 端前端（uni-app 小程序 / H5）
└── mall-admin/               # 管理后台前端（Vue3 + Element Plus）
```

## 技术栈

| 端     | 技术                                                                          |
| ----- | --------------------------------------------------------------------------- |
| C 端前端 | uni-app · Vue3 · Vite · SCSS · @dcloudio/uni-ui                             |
| 后台前端  | Vue3 · Vite · Element Plus · Vue Router · Pinia · Axios                     |
| 后端    | Python · FastAPI · SQLAlchemy 2.0 · Alembic · MySQL 8 · PyJWT · APScheduler |
| 质量    | pytest · ruff · mypy                                                        |

## 文档索引

以下文档是本项目的**唯一契约来源**，开发以它们为准：

| 文档                                                         | 内容                                                     |
| ---------------------------------------------------------- | ------------------------------------------------------ |
| [docs/prd.md](docs/prd.md)                                 | 产品需求（业务规则、状态机、验收口径）                                    |
| [docs/architecture.md](docs/architecture.md)               | 后端架构（分层、通用核心层、安全模型）                                    |
| [docs/api-design.md](docs/api-design.md)                   | 接口契约（路由、出入参、分页、响应体）                                    |
| [docs/database-design.md](docs/database-design.md)         | 数据契约（17 张表字段、约束、索引）                                    |
| [docs/test-cases.md](docs/test-cases.md)                   | 测试用例清单                                                 |
| [docs/conventions/](docs/conventions/)                     | 规范：error-code / auth / logging / environment / backend |
| [docs/integrations/wechat.md](docs/integrations/wechat.md) | 微信登录 / 支付对接说明                                          |
| [docs/sql/](docs/sql/)                                     | 数据库结构 schema.sql 与种子数据 seed-data.sql                   |

## 快速开始

### 后端（mall-backend）

```bash
cd mall-backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
cp .env.example .env          # 修改数据库连接、SECRET_KEY 等

# 建库（MySQL 8）并迁移
alembic upgrade head

# 启动服务，访问 http://127.0.0.1:8000/docs 查看接口文档
uvicorn app.main:app --reload
```

### 前端（mall-miniapp-uni）

```bash
cd mall-miniapp-uni
npm install

# 运行到微信小程序（微信开发者工具导入 dist/dev/mp-weixin）
npm run dev:mp-weixin

# 运行到 H5
npm run dev:h5
```

> 前端当前使用本地全仿真 mock 数据，`src/api/config.js` 的 `useMock` 可一键切换真实后端。

### 管理后台（mall-admin）

```bash
cd mall-admin
npm install

# 启动开发服务，访问 http://localhost:5174
npm run dev
```

> 默认账号 `admin` / `Admin@123456`（种子数据见 `docs/sql/seed-backend.sql`）。开发服务已配置代理，`/admin/api/*` 转发到后端 `http://127.0.0.1:8000`。

## 当前进度

- [x] 需求 / 架构 / 接口 / 数据库设计文档

- [x] 前端 12 个页面（mock 数据可运行）

- [x] 后端工程骨架（分层、迁移、auth 会员核心表）

- [x] 后端业务接口开发（P0：登录 → 首页/商品 → 购物车 → 地址 → 订单 → 收藏 → 会员中心）

- [x] P1：订单超时关闭、优惠券、积分流水、售后工单、管理后台（接口 + 可视化页面）

- [ ] P1 剩余：微信支付真实接入

## 说明

- 接口契约以 `docs/api-design.md` 为准，测试用例见 `docs/test-cases.md`。

- 业务实现遵循 `docs/conventions/` 下的 error-code / auth / logging 规范。

- 敏感信息（数据库密码、`SECRET_KEY`、密钥）仅存于 `mall-backend/.env`，已被 `.gitignore` 忽略，禁止提交。

