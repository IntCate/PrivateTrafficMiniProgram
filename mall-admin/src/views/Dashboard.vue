<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { Money, List, User, Clock } from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { getDashboardSummary, getDashboardTrend } from '@/api'
import { onWS } from '@/utils/ws'

echarts.use([LineChart, PieChart, GridComponent, TooltipComponent, CanvasRenderer])

const summary = ref({
  total_sales: '0.00',
  order_count: 0,
  member_count: 0,
  pending_order_count: 0,
})

const cards = ref([])

const trendEl = ref(null)
const catEl = ref(null)
const statusEl = ref(null)
let trendChart = null
let catChart = null
let statusChart = null

async function load() {
  summary.value = await getDashboardSummary()
  cards.value = [
    { label: '累计销售额', value: summary.value.total_sales, prefix: '¥', bg: 'linear-gradient(135deg, #0f172a, #334155)', icon: Money },
    { label: '订单总数', value: summary.value.order_count, bg: 'linear-gradient(135deg, #1e293b, #475569)', icon: List },
    { label: '待处理订单', value: summary.value.pending_order_count, bg: 'linear-gradient(135deg, #b45309, #f59e0b)', icon: Clock },
    { label: '会员总数', value: summary.value.member_count, bg: 'linear-gradient(135deg, #4c1d95, #8b5cf6)', icon: User },
  ]

  const trend = await getDashboardTrend()
  await nextTick()
  renderTrend(trend)
  renderCategory(trend)
  renderStatus(trend)
}

function renderTrend(t) {
  if (!trendChart) trendChart = trendEl.value && echarts.init(trendEl.value)
  if (!trendChart) return
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 48, top: 36, bottom: 24 },
    xAxis: { type: 'category', boundaryGap: false, data: t.days },
    yAxis: [
      { type: 'value', name: '销售额', splitLine: { lineStyle: { type: 'dashed' } } },
      { type: 'value', name: '订单数', splitLine: { show: false } },
    ],
    series: [
      {
        name: '销售额',
        type: 'line',
        smooth: true,
        symbolSize: 6,
        data: t.sales_trend.map(Number),
        itemStyle: { color: '#2563eb' },
        areaStyle: { opacity: 0.12 },
      },
      {
        name: '订单数',
        type: 'line',
        smooth: true,
        symbolSize: 6,
        yAxisIndex: 1,
        data: t.order_trend,
        itemStyle: { color: '#f59e0b' },
      },
    ],
  })
}

function renderCategory(t) {
  if (!catChart) catChart = catEl.value && echarts.init(catEl.value)
  if (!catChart) return
  catChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 个 ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['42%', '66%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        data: t.category_distribution,
      },
    ],
  })
}

function renderStatus(t) {
  if (!statusChart) statusChart = statusEl.value && echarts.init(statusEl.value)
  if (!statusChart) return
  statusChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 单 ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    color: ['#94a3b8', '#2563eb', '#f59e0b', '#10b981', '#ef4444', '#e2e8f0'],
    series: [
      {
        type: 'pie',
        radius: ['30%', '58%'],
        roseType: 'radius',
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        data: t.order_status_distribution,
      },
    ],
  })
}

function handleResize() {
  trendChart?.resize()
  catChart?.resize()
  statusChart?.resize()
}

onMounted(() => {
  load()
  onWS('order_new', load)
  onWS('catalog_changed', load)
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  catChart?.dispose()
  statusChart?.dispose()
})
</script>

<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col v-for="c in cards" :key="c.label" :span="6">
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

    <el-card shadow="never" class="panel">
      <template #header>
        <span class="panel-title">近7天销售趋势</span>
      </template>
      <div ref="trendEl" class="chart chart-lg" />
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card shadow="never" class="panel">
          <template #header>
            <span class="panel-title">分类商品占比</span>
          </template>
          <div ref="catEl" class="chart" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="panel">
          <template #header>
            <span class="panel-title">订单状态分布</span>
          </template>
          <div ref="statusEl" class="chart" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.panel {
  margin-top: 16px;
}
.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-1);
}
.chart {
  width: 100%;
  height: 320px;
}
.chart-lg {
  height: 360px;
}
.stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--border);
  box-shadow: var(--card-shadow);
  transition: all 0.25s ease;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
}
.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
  flex-shrink: 0;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}
.stat-info {
  flex: 1;
  min-width: 0;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-1);
  line-height: 1.2;
}
.stat-label {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-3);
}
</style>