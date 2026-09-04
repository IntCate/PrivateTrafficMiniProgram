# 通用规范 - 鉴权（auth）

> 双体系鉴权：**C 端会员**使用不透明 token（MySQL 会话表，可撤销）；**后台管理员**使用 JWT（无状态）。两套体系独立，互不通用。

---

## 1. C 端会员鉴权（token）

### 1.1 登录流程

```text
前端 uni.login() 拿 code
   → POST /api/auth/login { code }
   → 后端调微信 code2session { appid, secret, code } → openid
   → member 表查 openid：无 → 自动注册；有 → 直接登录
   → 生成 token → 写入 member_session（expires_at = now + 7d）
   → 返回 { token, member }
```

- 登录接口即使 member 被禁用也拒绝签发新 token；
- `openid` / `session_key` / `appSecret` **任何情况下不下发前端、不进日志**。

### 1.2 token 规范

| 项 | 约定 |
| --- | --- |
| 生成 | `secrets.token_urlsafe(32)`（约 43 字符，不可推断用户） |
| 存储 | `member_session` 表（见数据库设计 3.16），唯一索引 `uk_token` |
| 有效期 | 7 天（`expires_at` 惰性校验；每日定时任务兜底清理过期记录） |
| 传递 | `Authorization: Bearer {token}` |
| 多端 | 同用户可保留多会话；登出只删当前会话 |

### 1.3 校验与过期

- 每个 🔒 接口经依赖 `get_current_member` 校验：解析 Bearer → 查 `member_session`（存在且 `expires_at > NOW()`）→ 返回会员；
- 不存在/过期 → 返回 `401`，前端清除本地 token 并引导重新登录；
- 封禁处理：管理员禁用会员时删除其**全部** `member_session`，即刻生效。

### 1.4 越权防护（必遵）

- 所有带资源 ID 的 C 端接口（`/api/orders/{id}`、`/api/cart/{id}` 等）必须校验 **资源归属 `user_id == current_member.id`**，不匹配返回 `403`；
- 禁止仅凭"ID 查到数据"就放行。

## 2. 后台管理端鉴权（JWT + RBAC）

### 2.1 登录与签发

```text
POST /admin/api/login { username, password }
   → admin_user 表校验：账号存在、status=1、BCrypt 密码比对通过
   → 签发 JWT
```

- `payload`：`sub`（admin_id）、`role`（admin/operator/finance）、`exp`（12 小时）、`jti`（uuid，用于登出拉黑）；
- 认证密钥 `SECRET_KEY` 与会员 token 无关，仅存环境变量。

### 2.2 校验与角色

- 每请求先验签 + 校验 `exp`（无状态，不查库）；禁用管理员后其 JWT 在有效期内仍可用，如需即时失效走登出拉黑（`jti` 黑名单，预留）；
- RBAC 依赖 `require_roles("admin", "operator")`，按接口声明最小角色集；无权限返回 `403`（HTTP 状态码）；
- 权限矩阵（二期后台开发前固化）：

| 模块 | admin | operator | finance |
| --- | --- | --- | --- |
| 商品/分类/SKU | ✅ | ✅ | ❌ |
| 订单查询/发货 | ✅ | ✅ | ✅（查询） |
| 售后审核 | ✅ | ✅ | ❌ |
| 会员禁用 | ✅ | ❌ | ❌ |
| 优惠券/运营位 | ✅ | ✅ | ❌ |
| 系统配置 | ✅ | ❌ | ❌ |
| 数据概览 | ✅ | ✅ | ✅ |

## 3. FastAPI 依赖注入用法

```python
# 路由中直接声明依赖即可完成鉴权，业务函数拿到的是已鉴权对象

@router.get("/api/member/overview")
async def overview(member: Member = Depends(get_current_member)):
    ...

@router.put("/admin/api/products/{pid}/status")
async def update_status(
    admin: Admin = Depends(require_roles("operator", "admin")),
):
    ...
```

- `get_current_member`：解析会员 token（见 1.3）；
- `get_current_admin`：解析后台 JWT（见 2.2）；
- `require_roles(*names)`：在 `get_current_admin` 基础上追加角色白名单；
- 依赖统一在 `common/deps.py` 实现，业务模块禁止自造鉴权逻辑。

## 4. 安全红线清单

| 事项 | 要求 |
| --- | --- |
| `SECRET_KEY` / `WX_APP_SECRET` | 仅环境变量，禁止入库/进代码/进文档/进日志 |
| `session_key` | 仅服务端使用，用于手机号解密，禁止下发 |
| `openid` | 不作为接口入参/出参暴露（member 对外 ID 用自增 `id`） |
| 密码 | 一律 BCrypt 哈希；后台接口永不返回密码字段 |
| token/JWT | 日志与响应体一律脱敏（见 logging 规范） |