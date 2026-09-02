# 快乐购 - 自营私域商城小程序

基于 uni-app + Vue3 + Vite 实现的自营私域商城小程序，覆盖 12 个页面（首页、商品、商品详情、购物车、确认订单、订单列表/详情、收货地址、收藏、我的、设置），当前使用本地 mock 数据。

## 技术栈

- uni-app Vue3 + Vite
- SCSS
- @dcloudio/uni-ui（图标组件）

## 目录结构

```
mall-miniapp-uni/
├── index.html              # H5 运行入口（Vite 根目录入口必填，引用 /src/main.js）
├── pages/                  # 页面（12 个）
│   ├── index/              # 首页（tabBar）
│   ├── products/           # 商品页（tabBar）
│   ├── cart/               # 购物车页（tabBar）
│   ├── me/                 # 我的页（tabBar）
│   ├── product-detail/     # 商品详情页
│   ├── order-confirm/      # 确认订单页
│   ├── orders/             # 订单列表页
│   ├── order-detail/       # 订单详情页
│   ├── address/            # 收货地址列表页
│   ├── address-edit/       # 地址新增/编辑页
│   ├── favorites/          # 我的收藏页
│   └── settings/           # 设置页
├── api/                    # 请求层
│   ├── request.js          # 请求分发（mock 分流 / 真实后端）
│   ├── config.js           # 环境配置（useMock / BASE_URL / TOKEN_KEY）
│   ├── index.js            # 页面调用接口封装
│   └── mock/               # 全仿真 mock（状态机 + 业务 + 路由）
│       ├── store.js        # 状态与业务逻辑（种子数据、token、库存、订单状态机）
│       ├── routes.js       # 路由表（URL → store 方法）
│       └── index.js        # mock 出口
├── static/                 # 静态资源（图片）
├── App.vue
├── main.js
├── manifest.json
├── pages.json
├── vite.config.js
└── package.json
```

## 快速开始

```bash
# 进入项目目录
cd mall-miniapp-uni

# 安装依赖
npm install

# 运行到微信小程序
npm run dev:mp-weixin

# 运行到 H5
npm run dev:h5
```

> H5 运行入口为项目**根目录** `index.html`（引用 `/src/main.js`）。若缺失该文件，`npm run dev:h5` 访问根路径会报「找不到资源」，请勿删除。

## 页面说明

- **首页**：品牌入口、会员卡片（积分/优惠券）、运营横幅、主题精选、品牌承诺
- **商品页**：分类筛选、商品网格/列表视图
- **购物车**：商品列表、勾选/数量编辑、管理删除、结算栏
- **我的**：会员信息、订单状态入口（待付款/待发货角标）、功能菜单
- **商品详情**：商品轮播图、价格、SKU 选择、品牌承诺、底部操作栏
- **确认订单**：收货地址、商品明细、运费、结算预览
- **订单列表**：状态 tab 切换、取消/付款/提醒发货/确认收货/再次购买
- **订单详情**：状态描述、进度追踪、收货信息、底部操作
- **收货地址**：地址列表、默认地址、新增/编辑入口
- **地址编辑**：姓名/手机号/地区选择（`region` 数组）/详细地址
- **我的收藏**：收藏商品列表
- **设置**：联系方式、关于等入口

## 接口契约

当前为本地 mock 数据（`src/api/mock/store.js`，经 `src/api/request.js` 的 `mockRequest` 分流；`src/api/config.js` 的 `useMock` 可一键切换真实后端）。后端接口契约以 `docs/api-design.md` 为准，对接改造项见其中 §15「边界与风险」与 §16「mock 核对记录」。

### 已实现的关键业务口径

- **购物车失效项展示**：下架商品（`onSale:false`）或库存为 0 的购物车项**仍保留在购物车**，页面置灰 + 「已下架」角标 + 勾选锁定 + 数量控件隐藏，且**不参与金额合计**；勾选失效项结算按 `1203` 拦截，取消勾选即剔除。
- **全选语义**：全选只勾可售项，不勾失效项；取消全选清空全部勾选（保护「立即购买」直购链路）。
- **种子库**：内置 10 件商品，其中「云朵抱枕靠垫」预设 `onSale:false`（下架），用于验证 1203 结算拦截用例；配套购物车预置 4 项含该下架项并默认勾选。

## 设计特点

- 自营私域风格：弱化平台感，强化品牌与会员感
- 珊瑚红（#F54949）主色 + 暖米白（#FFFBF8）背景 + 暖金色（#E8B86D）点缀
- 商品展示统一采用「左图右详情」的杂志/清单式排版
