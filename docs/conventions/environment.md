# 通用规范 - 环境与接口联调（environment）

> 约定 dev / test / prod 三层环境的配置、域名、CORS、mock 开关与微信资质管理，保证前后端并行开发互不阻塞。

***

## 1. 环境划分

| 环境   | 用途       | 数据库               | 微信                                 | Base URL                            |
| ---- | -------- | ----------------- | ---------------------------------- | ----------------------------------- |
| dev  | 本地开发     | 本地 MySQL（可导入种子数据） | 使用测试小程序 appid 或 mock               | `http://127.0.0.1:8000/api`         |
| test | 前后端联调/验收 | 共享联调库             | 测试小程序 + 真实 code2session（可 mock 兜底） | `https://test-api.<domain>.com/api` |
| prod | 生产       | 生产库               | 正式小程序 + 商户号                        | `https://api.<domain>.com/api`      |

- 三层配置相互独立，各自 `dev.env` / `test.env` / `prod.env`（或环境变量注入），`.env*` 一律不进版本库；

- 环境切换由 `APP_ENV` 决定，禁止在代码中写死环境相关地址。

## 2. 配置项清单（`.env.example` 模板）

| 配置                                                            | 说明                     | 示例                                     |
| ------------------------------------------------------------- | ---------------------- | -------------------------------------- |
| `APP_ENV`                                                     | dev/test/prod          | `dev`                                  |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 连接               | `127.0.0.1 / 3306 / root / *** / mall` |
| `SECRET_KEY`                                                  | 后台 JWT 签名密钥（≥ 32 字符随机） | —                                      |
| `TOKEN_TTL_DAYS`                                              | C 端 token 有效期          | `7`                                    |
| `WX_APP_ID`                                                   | 小程序 appid              | `wxe93987e2facbdd4d`                   |
| `WX_APP_SECRET`                                               | 小程序密钥（**仅后端**）         | —                                      |
| `LOG_LEVEL`                                                   | DEBUG/INFO             | `INFO`                                 |
| `UPLOAD_DIR`                                                  | 头像/图片本地存储路径            | `uploads/`                             |
| `CORS_ORIGINS`                                                | 允许跨域来源（逗号分隔，见 §3）      | —                                      |
| `PAY_MODE`                                                    | mock/wechat（支付模式）      | `mock`                                 |

## 3. CORS 白名单

- **小程序** **`uni.request`** **不受浏览器 CORS 限制，不需要配跨域**；

- 需要 CORS 的是**后台管理 Web 端**与本地调试工具：

  - dev：允许 `http://localhost:*`、`http://127.0.0.1:*`；

  - test：允许后台联调域名；

  - prod：仅允许后台正式域名（若后台与 API 同域则无需放开）；

- CORS 来源白名单走 `CORS_ORIGINS` 配置，禁止 `*` 全放。

## 4. 联调约定

### 4.1 登录联调

- 未拿到正式 appid/secret 前：`LOGIN_MOCK` 开关开启，`code` 传任意值，后端本地生成稳定 openid（如 `mock_<code>`）即可跑通全链路；

- mock 开关只影响**后端**；小程序前端通过 `VITE_USE_MOCK` 决定是否走 mock 数据（`src/api/config.js`，默认 mock）。

- **前端本地联调配置**（`mall-miniapp-uni/.env.local`，不入仓库）：

  ```
  VITE_USE_MOCK=false
  VITE_API_BASE_URL=http://127.0.0.1:8000
  ```

  > 前端 `api/config.js` 的 BASE\_URL 默认值不含 `/api`，与接口路径拼接后为完整地址；`.env.local` 会覆盖默认值。

- **微信开发者工具登录联调步骤**（真实后端 + 真实 MySQL）：

  1. 先构建小程序产物：`mall-miniapp-uni` 下 `npm run build:mp-weixin`（产物在 `dist/build/mp-weixin`）；
  2. 开发者工具「导入项目」，目录选 `dist/build/mp-weixin`；
  3. **AppID 必须可获取** **`code`**：若产物内 appid 非本账号，改用「测试号」或本账号对应 AppID（`uni.login` 拿不到 code 时登录不触发）；
  4. 右上角「详情 → 本地设置」勾选 **「不校验合法域名、TLS 版本以及 HTTPS 证书」**（本地 http 方可访问）；
  5. 启动后小程序会自动静默登录（`App.vue onLaunch` → `uni.login` → `POST /api/auth/login` → 存 token）；后端日志应出现 `POST /api/auth/login 200 OK`。
  6. **登录未触发/怀疑旧 token 残留**：工具栏「清缓存 → 清除全部缓存」后重新编译（mock 模块只在 mock 模式写本地 token，真实模式不会注入假 token）。

- 真实联调前置条件：

  1. 微信公众平台已配置 **服务器域名**：`request` 合法域名 = API 域名、`uploadFile` 合法域名 = 文件域名；
  2. API 必须是 **HTTPS** 且证书受信；
  3. 后端配置 `WX_APP_ID` / `WX_APP_SECRET`。

### 4.2 支付联调

- `PAY_MODE=mock`：下单后接口直接模拟支付成功，前后端不依赖商户资质即可联调订单主链路；

- `PAY_MODE=wechat`（P1）：需商户号 + API v3 密钥 + 回调域名，回调验签细则见规划中的 [integrations/wechat.md](../integrations/wechat.md)（checklist §2.2 第 5 项）与微信官方文档。

### 4.3 数据与编号约定

| 项    | 约定                                            |
| ---- | --------------------------------------------- |
| 时间   | 统一 `Asia/Shanghai`，接口输出 `yyyy-MM-dd HH:mm:ss` |
| 订单号  | `K + yyyyMMddHHmmss + 3 位随机`（服务端生成）           |
| 金额   | 数字（或两位小数字符串），不带 `¥`，展示由前端处理                   |
| 种子数据 | `docs/sql/seed-data.sql` 与文档保持同步，各环境按需导入      |
| 上传域名 | 头像等静态资源走统一文件域名（生产建议 CDN/OSS 预留）               |

### 4.4 前端接入要点（源自 api-design §15）

- 前端目前购物车/订单/收藏/会员数据为本地 mock，切后端时**不迁移旧数据**（直接丢弃，从头开始）；

- 加入购物车需补 `skuId`（默认取首个 SKU）；详情页 SKU 改为接口动态渲染；

- `me.vue` 切 `/api/member/overview`；401 时清理 token 并回登录页。

## 5. 密钥与账号管理

| 项                                      | 管理要求                       |
| -------------------------------------- | -------------------------- |
| `WX_APP_SECRET` / `SECRET_KEY` / 数据库密码 | 仅限后端运维持有；禁止进前端、进文档、进日志、进仓库 |
| 小程序 appid                              | 文档中允许出现（非机密）               |
| 商户号/API v3 密钥                          | P1 申请后同样按密钥规范管理            |
| 管理员初始账号                                | 首次登录强制改密（见数据库设计种子数据注记）     |

