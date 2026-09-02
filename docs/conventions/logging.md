# 通用规范 - 日志（logging）

> 目标：日志可检索、可追踪、可审计、不泄露敏感信息。全链路统一 `request_id` 贯穿。

---

## 1. 级别约定

| 级别 | 使用场景 |
| --- | --- |
| DEBUG | 本地开发调试，测试/生产不输出 |
| INFO | 接口访问日志、业务关键动作（下单成功、支付回调、定时任务执行） |
| WARNING | 可恢复异常、限流命中、幂等重复操作 |
| ERROR | 业务异常未兜底、外部调用失败（微信接口）、数据一致性风险 |
| CRITICAL | 启动失败、数据库不可用等致命故障 |

## 2. 日志格式（JSON，单行）

```json
{
  "time": "2026-09-01 10:00:00.123",
  "level": "INFO",
  "logger": "app.api.v1.order",
  "request_id": "9f3c2a...",
  "method": "POST",
  "path": "/api/orders",
  "status": 200,
  "cost_ms": 45,
  "user_id": 1024,
  "ip": "1.2.3.4",
  "msg": "下单成功",
  "extra": {"order_no": "K20260901100000123"}
}
```

- 统一用结构化 logger（如 `structlog`/`logging` + JSON formatter），**禁止 print / 裸字符串日志**；
- 业务日志通过 `extra` 携带关联键（订单号、商品 ID），不拼接到 `msg`。

## 3. request_id 链路追踪

- 中间件为每个请求生成 `request_id`（`uuid4().hex`），写入日志 context 并回传响应头 `X-Request-Id`；
- 前端联调定位问题时报 `request_id` 即可全局检索该次请求全链路日志（访问日志 + 业务日志 + 错误日志）。

## 4. 访问日志（中间件统一产出）

每个请求一行 INFO，字段见第 2 节模板，覆盖：method、path、query、status、cost_ms、ip、user_id（登录后）。**不记录请求体与响应体**（防敏感数据入日志）。

## 5. 业务与审计日志

- C 端关键动作：登录、登出、下单、支付、取消、收货、改头像昵称（记 user_id + 动作 + 关键字段变更摘要）；
- 后台写操作必须审计：`{ admin_id, role, action, resource, resource_id, change（变更前/后摘要）, request_id, time }`；
- 审计日志单独文件/独立 logger（`audit`），保留期大于普通日志（建议 ≥ 180 天）。

## 6. 脱敏规则（统一实现于 `common/utils.py`）

| 字段 | 输出示例 |
| --- | --- |
| 手机号 | `138****1234` |
| token / JWT | 前 8 后 4（`abc12345****abcd`） |
| openid | 前 6 后 4（`oXXXXX****XXXX`） |
| session_key | **禁止记录** |
| 收货地址 | 省市区明文，详细地址打码（`****路88号`） |
| 支付参数/签名 | 禁止记录 |

所有日志输出前必须过脱敏函数，禁止在调用处手动拼接后再脱敏。

## 7. 错误日志

- 捕获未知异常时同时记录：异常类型、堆栈、请求上下文（path/params/request_id）、当前 user_id；
- 使用 `logger.exception`（自动带堆栈）或 `logger.error(..., exc_info=True)`；
- 堆栈中可能含入参的敏感字段，命中脱敏规则后输出。

## 8. 落地（Python）

| 项 | 方案 |
| --- | --- |
| 日志器 | `logging` + JSON Formatter（或 structlog） |
| request_id | FastAPI 中间件注入 contextvar |
| 文件 | 按日轮转 `logs/app-YYYYMMDD.log`、`logs/audit-YYYYMMDD.log`，保留 30 天（审计 180 天） |
| 级别 | dev=DEBUG / test=INFO / prod=INFO，ERROR 以上可配集中告警 |

## 9. 禁止事项

- 禁止打印：明文密码、token 全文、验证码、密钥、银行卡/身份证、session_key；
- 禁止将完整请求体/响应体写入日志；
- 禁止在循环内高频打 DEBUG 日志拖垮性能（正常链路 INFO 即可）。