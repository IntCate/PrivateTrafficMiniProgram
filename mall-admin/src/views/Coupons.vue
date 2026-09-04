<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { createCoupon, grantCoupon, listCoupons, updateCoupon } from '@/api'

const loading = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const form = reactive({ name: '', type: 'cash', amount: null, discount: null, min_amount: 0, total_count: 0, valid_start: null, valid_end: null, status: 1 })
const rules = {
  name: [{ required: true, message: '请输入券名称', trigger: 'blur' }],
}

const grantDialog = ref(false)
const current = ref(null)
const grantForm = reactive({ user_id: null, count: 1 })

async function load() {
  loading.value = true
  try {
    const data = await listCoupons()
    list.value = data.list
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', type: 'cash', amount: null, discount: null, min_amount: 0, total_count: 0, valid_start: null, valid_end: null, status: 1 })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    type: row.type,
    amount: row.amount != null ? Number(row.amount) : null,
    discount: row.discount != null ? Number(row.discount) : null,
    min_amount: Number(row.min_amount),
    total_count: row.total_count,
    valid_start: row.valid_start,
    valid_end: row.valid_end,
    status: row.status,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  if (editingId.value) {
    await updateCoupon(editingId.value, form)
    ElMessage.success('更新成功')
  } else {
    await createCoupon(form)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
}

function openGrant(row) {
  current.value = row
  grantForm.user_id = null
  grantForm.count = 1
  grantDialog.value = true
}

async function handleGrant() {
  if (!grantForm.user_id) {
    ElMessage.warning('请输入用户ID')
    return
  }
  await grantCoupon(current.value.id, grantForm)
  ElMessage.success('发放成功')
  grantDialog.value = false
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <el-card>
      <div class="toolbar">
        <el-button type="success" @click="openCreate">新增优惠券</el-button>
      </div>
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">{{ { cash: '满减', discount: '折扣', shipping: '包邮' }[row.type] || row.type }}</template>
        </el-table-column>
        <el-table-column label="面额/折扣" width="110">
          <template #default="{ row }">
            <span v-if="row.type === 'discount'">{{ row.discount }}折</span>
            <span v-else>¥{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="门槛" width="100">
          <template #default="{ row }">满¥{{ row.min_amount }}</template>
        </el-table-column>
        <el-table-column prop="total_count" label="总量" width="80" />
        <el-table-column prop="received_count" label="已领" width="80" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="primary" @click="openGrant(row)">发放</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑优惠券' : '新增优惠券'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio value="cash">满减</el-radio>
            <el-radio value="discount">折扣</el-radio>
            <el-radio value="shipping">包邮</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.type !== 'discount'" label="面额">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item v-else label="折扣">
          <el-input-number v-model="form.discount" :min="0" :max="1" :step="0.1" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="使用门槛">
          <el-input-number v-model="form.min_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="发放总量">
          <el-input-number v-model="form.total_count" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="生效时间">
          <el-date-picker v-model="form.valid_start" type="datetime" placeholder="生效时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="失效时间">
          <el-date-picker v-model="form.valid_end" type="datetime" placeholder="失效时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="grantDialog" title="发放优惠券" width="420px">
      <el-form label-width="90px">
        <el-form-item label="优惠券">
          <span>{{ current?.name }}</span>
        </el-form-item>
        <el-form-item label="用户ID">
          <el-input-number v-model="grantForm.user_id" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="grantForm.count" :min="1" :max="100" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="grantDialog = false">取消</el-button>
        <el-button type="primary" @click="handleGrant">确认发放</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  margin-bottom: 16px;
}
</style>
