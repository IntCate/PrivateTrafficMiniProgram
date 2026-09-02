# 微信对接说明（integrations/wechat）

> 快乐购商城与微信开放能力的对接文档：登录（code2session）、手机号、支付（P1）、头像昵称合规。
> 关联规范：[auth.md](../conventions/auth.md)（双体系鉴权）、[environment.md](../conventions/environment.md)（环境与联调）、[error-code.md](../conventions/error-code.md)。

***

## 1. 概览

| 能力                | 接口                                      | 状态             |
| ----------------- | --------------------------------------- | -------------- |
| 静默登录 code2session | `GET /sns/jscode2session`               | 已实现（含 mock）    |
| 手机号解密             | `POST /wxa/business/getuserphonenumber` | 预留             |
| 头像昵称填写            | 前端 `chooseAvatar` / `nickname`          | 前端已实现，后端校验见 §4 |
| 微信支付              | 统一下单 / 回调 / 退款                          | P1 预留          |

后端入口见 `mall-backend/app/integrations/wechat.py`（登录）与 `pay.py`（支付）。

***

## 2. 登录对接（C 端）

### 2.1 流程

```text
小程序 uni.login() → 临时 code
   → POST /api/auth/login { code, nickname?, avatar? }   [见 api-design §认证]
   → 后端:
       ① 调微信 code2session { appid, secret, js_code=code } → openid
       ② member 表按 openid 查：无 → 自动注册（默认等级 bronze）；有 → 登录
       ③ 校验 member.status=1（禁用则拒绝签发）
       ④ 生成 token → 写 member_session（expires_at = now + 7d）
       ⑤ 更新 last_login_at
   → 返回 { token, expiresIn, member }
```

### 2.2 code2session 调用参数

| 参数           | 值                                                      |
| ------------ | ------------------------------------------------------ |
| 接口           | `https://api.weixin.qq.com/sns/jscode2session`         |
| `appid`      | 小程序 appid（配置 `WX_APP_ID`）                              |
| `secret`     | 小程序密钥（配置 `WX_APP_SECRET`，**仅后端持有**）                    |
| `js_code`    | 前端传入的临时 code（一次性，5 分钟有效）                               |
| `grant_type` | `authorization_code`                                   |
| 返回           | `{ openid, session_key, unionid?, errcode?, errmsg? }` |

### 2.3 错误处理

- 微信返回 `errcode != 0`：按 [error-code.md](../conventions/error-code.md) 映射为业务错误码，前端统一弹提示；

- 常见微信错误：`40029`（code 无效/过期）、`45011`（频率限制）、`40163`（code 已使用）；

- **`openid`** **/** **`session_key`** **任何情况下不下发前端、不进日志**（见 auth.md §4 红线）。

### 2.4 LOGIN mock 开关

- `LOGIN_MOCK=true`（dev 默认）：跳过真实微信请求，后端按 `code` 生成稳定 `mock_<code>` openid，便于前端无资质跑通全链路；

- `LOGIN_MOCK=false`：走真实 code2session，需配置 `WX_APP_ID` / `WX_APP_SECRET`。

- 实现见 `wechat.py::code2session`：mock 分支优先返回。

***

## 3. 手机号解密（预留）

> 前端需用「手机号快速验证组件」`open-type="getPhoneNumber"` 获取 `code`（非手机号明文）。

- 接口：`POST https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}`，body `{ "code": "..." }`；

- 依赖 `access_token`（`client_credential` 换取，需缓存）与 `session_key` 解密流程；

- 落地时机：P1；未实现前 `member.phone` 由用户手动填写或置空。

***

## 4. 头像昵称（合规，P0）

遵循 PRD §4.9：

| 项  | 前端                                                          | 后端校验                                 |
| -- | ----------------------------------------------------------- | ------------------------------------ |
| 头像 | `button open-type="chooseAvatar"` 选择 → 上传到自有服务存储 → 提交永久 URL | 校验头像 URL 属于**自有存储域**，禁止客户端直接提交外部 URL |
| 昵称 | `input type="nickname"` 由微信键盘辅助填写                           | 长度 1-20 字；过滤敏感词                      |

- 头像上传接口：`POST /api/upload`（见 api-design 上传章节），文件落地 `UPLOAD_DIR`；

- 完成接口：`PUT /api/member/profile`（nickname/avatar）。

***

## 5. 微信支付（P1 预留）

### 5.1 前置资质（P1 申请）

| 项                                | 说明                          |
| -------------------------------- | --------------------------- |
| 微信支付商户号                          | `mchid`，需企业资质申请             |
| API v3 密钥                        | 平台证书加密/解密回调                 |
| 商户 API 证书（apiclient\_cert / key） | 请求签名                        |
| 回调域名                             | 需在商户平台配置，且与后台 `WX_PAY` 配置一致 |

### 5.2 下单与回调流程（目标设计）

```text
前端 请求支付 → POST /api/orders/{id}/pay
   → 后端校验订单状态=pending，按 PAY_MODE 分支:
      mock   : 直接置 paid，返回成功（当前已可用）
      wechat : 调统一下单 → 返回 prepay 参数（timeStamp/nonceStr/package/signType/paySign）
   → 前端 wx.requestPayment() 拉起收银台
   → 微信支付成功 → 回调 notify_url 验签 → 置订单 paid、扣真实库存并释放锁存
```

- 回调验签必须做：平台公钥 + 签名校验 + 金额/商户单号一致性校验，防伪造回调；

- 幂等：回调可能重复，按 `transaction_id` 或订单状态做幂等处理；

- 下单即预占库存（`lock_stock += qty`），支付成功后 `stock -= qty` 并 `lock_stock -= qty`（见 database-design §6）。

### 5.3 退款（订单级，P1）

- `POST /api/orders/{id}/refund`（api-design §9.7）先落 `orders` 表（置 status=refund + refund\_\* 字段）；

- 真实资金退回走微信退款接口，落 `after_sale` 工单（P1 扩展）。

***

## 6. 密钥与配置清单

| 配置键（.env）       | 用途              | 归属         |
| --------------- | --------------- | ---------- |
| `WX_APP_ID`     | 小程序 appid       | 可入文档\*\*   |
| `WX_APP_SECRET` | code2session 密钥 | **仅后端**    |
| `LOGIN_MOCK`    | 登录 mock 开关      | 后端         |
| `PAY_MODE`      | pay mock/wechat | 后端         |
| `WX_PAY_*`（规划）  | 商户号/密钥/证书       | **仅后端，P1** |

> **安全红线**：`WX_APP_SECRET`、商户密钥、API v3 密钥、支付证书一律**仅存环境变量**，禁止落入仓库、文档、代码字面量、日志。`.env*` 已列入 `.gitignore`。

***

## 7. 域名与资质（联调前置）

见 `environment.md §4.1`：

1. 微信公众平台 → 开发管理 → 服务器域名，配置 `request` 合法域名 = API 域名、`uploadFile` 合法域名 = 文件域名；
2. API 必须 **HTTPS** 且证书受信；
3. 登录前确认 `WX_APP_ID` / `WX_APP_SECRET` 已配置。

***

## 8. 相关文件索引

| 位置                                        | 内容                                  |
| ----------------------------------------- | ----------------------------------- |
| `mall-backend/app/integrations/wechat.py` | code2session / getPhoneNumber（骨架）   |
| `mall-backend/app/integrations/pay.py`    | 支付（P1 占位）                           |
| `docs/conventions/auth.md`                | 登录/token/安全红线                       |
| `docs/conventions/environment.md`         | 环境、mock、域名资质                        |
| `docs/api-design.md`                      | 认证/会员/上传接口契约                        |
| `docs/sql/schema.sql`                     | member / member\_session / orders 表 |

