<script setup>
import { onMounted, ref } from 'vue'

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
    { label: '累计销售额（元）', value: summary.value.total_sales, color: '#409eff' },
    { label: '订单总数', value: summary.value.order_count, color: '#67c23a' },
    { label: '会员总数', value: summary.value.member_count, color: '#e6a23c' },
    { label: '商品总数', value: summary.value.product_count, color: '#f56c6c' },
    { label: '待处理订单', value: summary.value.pending_order_count, color: '#909399' },
  ]
}

onMounted(load)
</script>

<template>
  <div>
    <el-row :gutter="16">
      <el-col v-for="c in cards" :key="c.label" :span="4.8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" :style="{ color: c.color }">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-card {
  text-align: center;
  margin-bottom: 16px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
}
.stat-label {
  margin-top: 8px;
  color: #909399;
  font-size: 13px;
}
</style>
