<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { listOrders, shipOrder } from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ page: 1, pageSize: 10, status: '' })

const statusMap = {
  pending: '待付款',
  paid: '待发货',
  shipped: '待收货',
  completed: '已完成',
  cancelled: '已取消',
  refund: '已退款',
}

const statusOptions = Object.entries(statusMap).map(([value, label]) => ({ value, label }))

const shipDialog = ref(false)
const currentOrder = ref(null)
const trackingNo = ref('')

async function load() {
  loading.value = true
  try {
    const data = await listOrders(query)
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  load()
}

function openShip(row) {
  currentOrder.value = row
  trackingNo.value = ''
  shipDialog.value = true
}

async function handleShip() {
  await shipOrder(currentOrder.value.id, { tracking_no: trackingNo.value || null })
  ElMessage.success('发货成功')
  shipDialog.value = false
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <el-card>
      <div class="toolbar">
        <el-select v-model="query.status" placeholder="订单状态" clearable style="width: 160px" @change="handleSearch">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="user_id" label="用户ID" width="80" />
        <el-table-column label="金额" width="110">
          <template #default="{ row }">¥{{ row.pay_amount }}</template>
        </el-table-column>
        <el-table-column prop="receiver_name" label="收货人" width="100" />
        <el-table-column prop="receiver_phone" label="电话" width="130" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'paid' ? 'warning' : row.status === 'completed' ? 'success' : 'info'">
              {{ statusMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="下单时间" width="170" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'paid'" size="small" type="primary" @click="openShip(row)">发货</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.pageSize"
        :total="total"
        layout="total, prev, pager, next"
        class="pager"
        @current-change="load"
      />
    </el-card>

    <el-dialog v-model="shipDialog" title="订单发货" width="420px">
      <el-form label-width="90px">
        <el-form-item label="订单号">
          <span>{{ currentOrder?.order_no }}</span>
        </el-form-item>
        <el-form-item label="物流单号">
          <el-input v-model="trackingNo" placeholder="请输入物流单号（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipDialog = false">取消</el-button>
        <el-button type="primary" @click="handleShip">确认发货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
