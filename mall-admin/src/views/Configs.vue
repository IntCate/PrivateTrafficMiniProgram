<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { listConfigs, updateConfig } from '@/api'

const loading = ref(false)
const list = ref([])
const editingKey = ref('')
const editValue = ref('')
const editRemark = ref('')
const dialogVisible = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await listConfigs()
    list.value = data.list
  } finally {
    loading.value = false
  }
}

function openEdit(row) {
  editingKey.value = row.config_key
  editValue.value = row.config_value
  editRemark.value = row.remark || ''
  dialogVisible.value = true
}

async function handleSave() {
  await updateConfig(editingKey.value, { config_value: editValue.value, remark: editRemark.value || null })
  ElMessage.success('保存成功')
  dialogVisible.value = false
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <el-card>
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="config_key" label="配置键" width="220" />
        <el-table-column prop="config_value" label="配置值" min-width="200" show-overflow-tooltip />
        <el-table-column prop="remark" label="说明" min-width="160" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="编辑配置" width="520px">
      <el-form label-width="90px">
        <el-form-item label="配置键">
          <el-input :model-value="editingKey" disabled />
        </el-form-item>
        <el-form-item label="配置值">
          <el-input v-model="editValue" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="editRemark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
