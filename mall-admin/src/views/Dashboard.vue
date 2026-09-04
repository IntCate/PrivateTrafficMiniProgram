<script setup>
import { onMounted, ref } from 'vue'
import { Money, List, User, Goods, Clock } from '@element-plus/icons-vue'

import { getDashboardSummary } from '@/api'

const summary = ref({
  total_sales: '0.00',
  order_count: 0,
  member_count: 0,
  product_count: 0,
  pending_order_count: 0,
})

const cards = ref([])

async function load() {
  summary.value = await getDashboardSummary()
  cards.value = [
    { label: '累计销售额', value: summary.value.total_sales, prefix: '¥', color: '#0d9488', bg: 'linear-gradient(135deg, #0d9488, #14b8a6)', icon: Money },
    { label: '订单总数', value: summary.value.order_count, color: '#3b82f6', bg: 'linear-gradient(135deg, #3b82f6, #60a5fa)', icon: List },
    { label: '会员总数', value: summary.value.member_count, color: '#f59e0b', bg: 'linear-gradient(135deg, #f59e0b, #fbbf24)', icon: User },
    { label: '商品总数', value: summary.value.product_count, color: '#8b5cf6', bg: 'linear-gradient(135deg, #8b5cf6, #a78bfa)', icon: Goods },
    { label: '待处理订单', value: summary.value.pending_order_count, color: '#ef4444', bg: 'linear-gradient(135deg, #ef4444, #f87171)', icon: Clock },
  ]
}

onMounted(load)
</script>

<template>
  <div>
    <el-row :gutter="20">
      <el-col v-for="c in cards" :key="c.label" :span="4.8">
        <div class="stat-card">
          <div class="stat-icon" :style="{ background: c.bg }">
            <el-icon><component :is="c.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              <span v-if="c.prefix">{{ c.prefix }}</span>{{ c.value }}
            </div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card class="welcome-card">
          <div class="welcome-content">
            <div>
              <h2>欢迎使用快乐购管理后台 👋</h2>
              <p>在这里您可以管理商品、订单、会员、营销活动等，高效运营您的私域商城。</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 22px;
  display: flex;
  align-items: center;
  gap: 18px;
  border: 1px solid var(--border);
  box-shadow: var(--card-shadow);
  transition: all 0.25s ease;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 26px;
  flex-shrink: 0;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}
.stat-info {
  flex: 1;
  min-width: 0;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-1);
  line-height: 1.2;
}
.stat-label {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-3);
}

.welcome-card {
  padding: 32px;
}
.welcome-content h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: 10px;
}
.welcome-content p {
  font-size: 14px;
  color: var(--text-2);
  line-height: 1.7;
}
</style>
