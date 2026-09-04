# 快乐购 · 管理后台

快乐购商城的管理后台前端，基于 Vue3 + Vite + Element Plus 构建，对接 `mall-backend` 的 `/admin/api/*` 接口。

## 技术栈

- Vue 3（`<script setup>`）
- Vite
- Element Plus + @element-plus/icons-vue
- Vue Router 4（鉴权路由守卫 + 角色权限）
- Pinia（用户状态）
- Axios（统一请求封装，自动携带 JWT）

## 快速开始

```bash
npm install
npm run dev        # 开发服务，默认 http://localhost:5174
npm run build      # 生产构建
```

> 开发服务已配置代理：`/admin/api/*` 转发到后端 `http://127.0.0.1:8000`，无需处理跨域。

## 默认账号

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| admin | Admin@123456 | 超级管理员 |

> 种子数据见 `docs/sql/seed-backend.sql`，须先执行 `alembic upgrade head` 建表后导入。

## 页面与权限

| 页面 | 路由 | 角色 |
| --- | --- | --- |
| 数据概览 | /dashboard | admin / operator / finance |
| 商品管理 | /products | admin / operator |
| 分类管理 | /categories | admin / operator |
| 订单管理 | /orders | admin / operator / finance |
| 售后管理 | /after-sales | admin / operator |
| 会员管理 | /members | admin / operator / finance |
| 运营位管理 | /banners | admin / operator |
| 优惠券管理 | /coupons | admin / operator |
| 系统配置 | /configs | admin |
| 管理员管理 | /admins | admin |

## 目录结构

```
src/
├── api/            # 接口封装
├── layout/         # 后台布局（侧边栏 + 顶栏）
├── router/         # 路由 + 鉴权守卫
├── store/          # Pinia 状态
├── utils/          # axios 请求封装
└── views/          # 页面
```
