# 通用规范 - 后端代码规范（backend）

> 快乐购商城后端（`mall-backend/`，FastAPI + SQLAlchemy）的工程化规范：目录、分层、命名、质量门禁与提交约定。
> 关联文档：[architecture.md](../architecture.md)、[api-design.md](../api-design.md)、[database-design.md](../database-design.md)、同目录下 auth / error-code / logging / environment 规范。

***

## 1. 分层结构与依赖方向

```text
api（路由） → service（业务） → repository（数据访问） → models（ORM）
```

- **单向依赖**：禁止跨层、跨模块直接 import 数据访问；api 层不裸查数据库；

- 每业务模块 `modules/<name>/` 内含：

  ```text
  modules/auth/
  ├── __init__.py      # 预留 service 层出口
  ├── api.py           # 路由 + 出入参校验
  ├── models.py        # ORM 模型（对齐 database-design）
  ├── repository.py    # 数据访问（继承 common/repository.py 仓储基类）
  ├── schemas.py       # Pydantic 出入参（继承 common/schemas.py 驼峰基类）
  └── service.py       # 业务逻辑（可选，按需新增）
  ```

- 通用能力（鉴权、分页、异常、响应、日志、上传、仓储基类）统一收敛在 `core/` 与 `common/`，业务模块禁止自造。

## 2. 命名约定

| 对象                  | 风格                               | 示例                                 |
| ------------------- | -------------------------------- | ---------------------------------- |
| 表 / 字段 / 模型属性       | snake\_case                      | `member_level`、`order_item`        |
| 数据库表名               | 小写复数                             | `orders`（避让关键字）                    |
| Python 类（ORM/Model） | PascalCase                       | `Member`、`ProductSku`              |
| Python 函数 / 方法      | snake\_case                      | `get_current_member`               |
| 路由文件函数              | snake\_case + 路由前缀匹配             | `list_products`、`get_order_detail` |
| 常量                  | UPPER\_SNAKE                     | `MEMBER_LEVEL_DEFAULT`             |
| API 出入参字段（对外）       | **驼峰**（由 `common/schemas.py` 别名） | `memberLevel`、`pageSize`           |

- **Pydantic 字段用 snake\_case 声明**，`CamelModel/CamelRequest` 基类自动转对外驼峰（见 common/schemas.py）。

## 3. 分层职责速查

| 层               | 职责                             | 禁止             |
| --------------- | ------------------------------ | -------------- |
| `api.py`        | 路由定义、依赖注入（鉴权/分页）、schema 绑定     | 拼 SQL、业务决策     |
| `service.py`    | 业务规则（状态机、库存、金额、幂等）、事务编排        | 直接返回 ORM 对象给前端 |
| `repository.py` | SELECT/INSERT/UPDATE 封装、仓储基类复用 | 业务规则           |
| `models.py`     | 字段/索引/关系声明，对齐 database-design  | 业务逻辑           |

## 4. 接口实现约定

- **统一响应体**：`{ code, message, data }`，见 `core/response.py` 与 [error-code.md](error-code.md)；成功 `code=0`；

- **错误处理**：业务错误抛 `BizException(code, message)`，由全局 handler 统一转 JSON（见 `core/exceptions.py`）；禁止在路由里手写 try/except 包一层；

- **鉴权**：一律走 `common/deps.py` 依赖（`get_current_member` / `get_current_admin` / `require_roles`），业务函数只拿已鉴权对象（见 [auth.md](auth.md)）；

- **分页**：出参 `{ list, total, page, pageSize, hasMore }`，入参 `page/pageSize`（别名驼峰），复用 `core/response.py` 分页对象；

- **金额**：用 `Decimal` 计算，接口回数字不带 `¥`；

- **字段转换**：对外字段用 Pydantic schema 转换，禁止手工拼 dict/to\_dict 返回 ORM。

## 5. 事务与数据一致性

- 跨表写操作放同一个 `db` 会话事务；显式 `commit` 失败统一回滚；

- 库存扣减、优惠券/积分发放必须 `SELECT ... FOR UPDATE` 行锁（见 database-design §6）；

- 软删表（member / member_session / product / product_sku / orders / shipping_address）默认查询必须带 `deleted=0` 过滤（各 repository/service 显式过滤，见 database-design §1.3）；

- 时间统一存 MySQL `DATETIME`，输出 `yyyy-MM-dd HH:mm:ss`；

- 幂等操作（支付回调、超时关闭）要可重复执行且无害。

## 6. 配置与密钥

- 一切环境差异走 `.env` / `pydantic-settings`（`core/config.py`），禁止代码里写死 IP、密钥、域名、环境地址；

- `SECRET_KEY` / 数据库密码 / `WX_APP_SECRET` / 支付密钥**仅环境变量**，禁止落库/落码/落日志/落文档；

- `.env*` 已在 `.gitignore` 排除，仓库只提交 `.env.example`。

## 7. 质量门禁（提交前必须通过）

| 工具      | 命令                     | 要求                                                        |
| ------- | ---------------------- | --------------------------------------------------------- |
| ruff    | `ruff check app/`      | 0 错误（契约性驼峰字段/`BizException` 命名在 `pyproject.toml` 豁免并注明依据） |
| mypy    | `mypy app`             | 0 错误                                                      |
| pytest  | `pytest`               | 全绿                                                        |
| alembic | `alembic upgrade head` | 迁移可执行                                                     |

- 改动数据库字段 → 同步 `models.py` + 新增 alembic 迁移 + 更新 [database-design.md](../database-design.md)；

- 改动接口 → 同步 [api-design.md](../api-design.md) 与 `docs/sql` 种子数据。

## 8. 提交约定（git）

- 分支：主基线 `main`，功能分支 `feat/<module>-<desc>`；

- 提交信息用 Conventional Commits：

  - `feat:` 新功能 / `fix:` 修复 / `docs:` 文档 / `refactor:` 重构 / `test:` 测试 / `chore:` 工程 / `perf:` 性能；

  - 示例：`feat(auth): 实现微信登录与会员会话`、`docs(sql): 新增表结构与种子数据`；

- 一次提交聚焦单一改动；禁止把密钥、构建产物、`.env` 提交。

## 9. 测试约定

- `tests/unit/`：纯函数与工具（脱敏、分页、金额计算、token 掩码）；

- `tests/api/`：接口集成测试（TestClient），校验统一响应体与错误码；

- 命名 `test_<对象>.py`，函数 `test_<行为>`；断言用 `assert`，禁止打印调试残留。

