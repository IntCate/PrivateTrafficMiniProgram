<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  DataAnalysis,
  Goods,
  Menu,
  Tickets,
  User,
  Setting,
  ShoppingCart,
  Service,
  Picture,
  SwitchButton,
  Shop,
} from '@element-plus/icons-vue'

import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const role = computed(() => userStore.role)

const menus = [
  { path: '/dashboard', title: '数据概览', icon: DataAnalysis, roles: ['admin', 'operator', 'finance'] },
  { path: '/products', title: '商品管理', icon: Goods, roles: ['admin', 'operator'] },
  { path: '/categories', title: '分类管理', icon: Menu, roles: ['admin', 'operator'] },
  { path: '/orders', title: '订单管理', icon: ShoppingCart, roles: ['admin', 'operator', 'finance'] },
  { path: '/after-sales', title: '售后管理', icon: Service, roles: ['admin', 'operator'] },
  { path: '/members', title: '会员管理', icon: User, roles: ['admin', 'operator', 'finance'] },
  { path: '/banners', title: '运营位管理', icon: Picture, roles: ['admin', 'operator'] },
  { path: '/coupons', title: '优惠券管理', icon: Tickets, roles: ['admin', 'operator'] },
  { path: '/configs', title: '系统配置', icon: Setting, roles: ['admin'] },
  { path: '/admins', title: '管理员管理', icon: User, roles: ['admin'] },
]

const visibleMenus = computed(() => menus.filter((m) => m.roles.includes(role.value)))

const activeMenu = computed(() => route.path)

const roleText = computed(() => {
  const map = { admin: '超级管理员', operator: '运营', finance: '财务' }
  return map[role.value] || role.value
})

const roleColor = computed(() => {
  const map = { admin: '#0d9488', operator: '#f59e0b', finance: '#6366f1' }
  return map[role.value] || '#64748b'
})

async function handleLogout() {
  await ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="232px" class="aside">
      <div class="logo">
        <el-icon class="logo-icon"><Shop /></el-icon>
        <span class="logo-text">快乐购后台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="transparent"
        text-color="#94a3b8"
        active-text-color="#14b8a6"
      >
        <el-menu-item v-for="m in visibleMenus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="page-title">
          <span class="breadcrumb-label">管理后台</span>
          <span class="breadcrumb-sep">/</span>
          <span class="page-name">{{ route.meta.title }}</span>
        </div>
        <div class="user-area">
          <el-tag class="role-tag" :color="roleColor + '14'" :border-color="roleColor + '33'" effect="plain">
            <span class="role-dot" :style="{ background: roleColor }"></span>
            {{ roleText }}
          </el-tag>
          <div class="user-info">
            <div class="avatar">{{ (userStore.admin?.nickname || userStore.admin?.username || 'A').charAt(0) }}</div>
            <span class="username">{{ userStore.admin?.nickname || userStore.admin?.username }}</span>
          </div>
          <el-button text class="logout-btn" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
}
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 22px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.logo-icon {
  font-size: 22px;
  color: var(--primary-light);
}
.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}
.aside :deep(.el-menu) {
  border-right: none;
  padding-top: 10px;
}
.aside :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  margin: 3px 12px !important;
  border-radius: 8px;
  color: #94a3b8;
}
.aside :deep(.el-menu-item:hover) {
  background: var(--sidebar-hover) !important;
  color: #fff;
}
.aside :deep(.el-menu-item.is-active) {
  background: var(--sidebar-active-bg) !important;
  color: var(--sidebar-active-text) !important;
  font-weight: 600;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 28px;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-light);
}
.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.breadcrumb-label {
  color: var(--text-3);
  font-size: 14px;
}
.breadcrumb-sep {
  color: var(--text-3);
}
.page-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-1);
}
.user-area {
  display: flex;
  align-items: center;
  gap: 14px;
}
.role-tag {
  height: 28px !important;
  padding: 0 12px !important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.role-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}
.username {
  color: var(--text-2);
  font-size: 14px;
}
.logout-btn {
  color: var(--text-3) !important;
}
.logout-btn:hover {
  color: var(--danger) !important;
}
.main {
  background: var(--main-bg);
  padding: 24px;
}
</style>
