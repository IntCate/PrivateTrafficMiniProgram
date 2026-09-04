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

async function handleLogout() {
  await ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="210px" class="aside">
      <div class="logo">快乐购 · 管理后台</div>
      <el-menu :default-active="activeMenu" router background-color="#001529" text-color="#a6adb4" active-text-color="#fff">
        <el-menu-item v-for="m in visibleMenus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="page-title">{{ route.meta.title }}</div>
        <div class="user-area">
          <el-tag size="small" type="info">{{ roleText }}</el-tag>
          <span class="username">{{ userStore.admin?.nickname || userStore.admin?.username }}</span>
          <el-button text @click="handleLogout">
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
  background: #001529;
}
.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  background: #002140;
}
.aside :deep(.el-menu) {
  border-right: none;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
  background: #fff;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
}
.user-area {
  display: flex;
  align-items: center;
  gap: 10px;
}
.username {
  color: #333;
}
.main {
  background: #f0f2f5;
}
</style>
