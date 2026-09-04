<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { auditAfterSale, listAfterSales } from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ page: 1, pageSize: 10, status: '' })

const typeMap = { refund: '退款', return: '退货退款' }
const statusMap = { applying: '待审核', approved: '已通过', rejected: '已拒绝' }

const auditDialog = ref(false)
const current = ref(null)
const approve = ref(true)
const remark = ref('')

async function load() {
  loading.value = true
  try {
    const data = await listAfterSales(query)
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openAudit(row, isApprove) {
  current.value = row
  approve.value = isApprove
  remark.value = ''
  auditDialog.value = true
}

async function handleAudit() {
  await auditAfterSale(current.value.id, { approve: approve.value, remark: remark.value || null })
  ElMessage.success(approve.value ? '已通过' : '已拒绝')
  auditDialog.value = false
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <el-card>
      <div class="toolbar">
        <el-select v-model="query.status" placeholder="售后状态" clearable style="width: 160px" @change="load">
          <el-option v-for="(label, value) in statusMap" :key="value" :label="label" :value="value" />
        </el-select>
      </div>

      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="order_id" label="订单ID" width="90" />
        <el-table-column prop="user_id" label="用户ID" width="90" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">{{ typeMap[row.type] || row.type }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="160" show-overflow-tooltip />
        <el-table-column label="金额" width="100">
          <template #default="{ row }">¥{{ row.amount }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'applying' ? 'warning' : row.status === 'approved' ? 'success' : 'info'">
              {{ statusMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'applying'">
              <el-button size="small" type="success" @click="openAudit(row, true)">通过</el-button>
              <el-button size="small" type="danger" @click="openAudit(row, false)">拒绝</el-button>
            </template>
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

    <el-dialog v-model="auditDialog" :title="approve ? '通过售后' : '拒绝售后'" width="420px">
      <el-form label-width="90px">
        <el-form-item label="售后单">
          <span>#{{ current?.id }}（订单 {{ current?.order_id }}）</span>
        </el-form-item>
        <el-form-item label="审核备注">
          <el-input v-model="remark" type="textarea" :rows="3" placeholder="请输入审核备注（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auditDialog = false">取消</el-button>
        <el-button :type="approve ? 'success' : 'danger'" @click="handleAudit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
