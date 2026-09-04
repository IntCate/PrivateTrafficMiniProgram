import { createRouter, createWebHistory } from 'vue-router'

import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layout/Index.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据概览', roles: ['admin', 'operator', 'finance'] },
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/Products.vue'),
        meta: { title: '商品管理', roles: ['admin', 'operator'] },
      },
      {
        path: 'categories',
        name: 'Categories',
        component: () => import('@/views/Categories.vue'),
        meta: { title: '分类管理', roles: ['admin', 'operator'] },
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/Orders.vue'),
        meta: { title: '订单管理', roles: ['admin', 'operator', 'finance'] },
      },
      {
        path: 'after-sales',
        name: 'AfterSales',
        component: () => import('@/views/AfterSales.vue'),
        meta: { title: '售后管理', roles: ['admin', 'operator'] },
      },
      {
        path: 'members',
        name: 'Members',
        component: () => import('@/views/Members.vue'),
        meta: { title: '会员管理', roles: ['admin', 'operator', 'finance'] },
      },
      {
        path: 'banners',
        name: 'Banners',
        component: () => import('@/views/Banners.vue'),
        meta: { title: '运营位管理', roles: ['admin', 'operator'] },
      },
      {
        path: 'coupons',
        name: 'Coupons',
        component: () => import('@/views/Coupons.vue'),
        meta: { title: '优惠券管理', roles: ['admin', 'operator'] },
      },
      {
        path: 'configs',
        name: 'Configs',
        component: () => import('@/views/Configs.vue'),
        meta: { title: '系统配置', roles: ['admin'] },
      },
      {
        path: 'admins',
        name: 'Admins',
        component: () => import('@/views/Admins.vue'),
        meta: { title: '管理员管理', roles: ['admin'] },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const userStore = useUserStore()
  if (to.meta.public) return true
  if (!userStore.isLoggedIn) return { path: '/login' }
  const roles = to.meta.roles
  if (roles && !roles.includes(userStore.role)) {
    return { path: '/dashboard' }
  }
  return true
})

export default router
