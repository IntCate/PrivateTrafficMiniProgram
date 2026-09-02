# 快乐购商城 - 后端

基于 FastAPI + SQLAlchemy + MySQL 8 的自营私域商城后端，按 `docs/architecture.md` 骨架搭建。

## 技术栈

- Python 3.11+ / FastAPI / Uvicorn
- SQLAlchemy 2.0 + PyMySQL + Alembic
- Pydantic 2 + pydantic-settings
- PyJWT（后台）+ passlib/bcrypt（密码）
- APScheduler（定时任务）
- pytest / ruff / mypy

## 目录结构

```
mall-backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── core/                # 通用核心层（配置/数据库/异常/响应/安全/日志/调度）
│   ├── common/              # 通用工具层（依赖/枚举/工具/上传/仓储基类）
│   ├── modules/             # 业务模块（auth/member/product/cart/address/order/favorite/after_sale/admin/coupon/points）
│   ├── integrations/        # 三方对接（微信/支付）
│   └── api/v1/router.py     # 路由统一注册点
├── alembic/                 # 数据库迁移
├── tests/                   # tests/unit、tests/api
├── scripts/                 # 初始化脚本
├── .env.example
├── requirements.txt
└── pyproject.toml           # ruff / mypy 配置
```

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt

# 2. 配置环境变量
cp .env.example .env         # 修改数据库连接、SECRET_KEY 等

# 3. 数据库迁移（需先建库 mall）
alembic upgrade head

# 4. 启动服务
uvicorn app.main:app --reload
# 访问 http://127.0.0.1:8000/docs 查看接口文档
```

## 质量检查

```bash
ruff check .
mypy app
pytest
```

## 规范

- 统一响应 `{code, message, data}`，错误码见 `docs/conventions/error-code.md`
- 双体系鉴权（C 端 token + 后台 JWT/RBAC），见 `docs/conventions/auth.md`
- 分层依赖：api → service → repository → models，禁止跨层/跨模块直接 import repository
- 接口契约以 `docs/api-design.md` 为准，测试用例见 `docs/test-cases.md`
