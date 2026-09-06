<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, RefreshRight } from '@element-plus/icons-vue'

import { createBanner, deleteBanner, listBanners, updateBanner, uploadImage } from '@/api'
import { onWS } from '@/utils/ws'

const loading = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const form = reactive({ position: 'hero', title: '', sub_title: '', image: '', link_type: 'none', link_value: '', sort: 0, status: 1 })
const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  image: [{ required: true, message: '请输入图片地址', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const data = await listBanners()
    list.value = data.list
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { position: 'hero', title: '', sub_title: '', image: '', link_type: 'none', link_value: '', sort: 0, status: 1 })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    position: row.position,
    title: row.title,
    sub_title: row.sub_title || '',
    image: row.image,
    link_type: row.link_type,
    link_value: row.link_value || '',
    sort: row.sort,
    status: row.status,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  if (editingId.value) {
    await updateBanner(editingId.value, form)
    ElMessage.success('更新成功')
  } else {
    await createBanner(form)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
}

// 图片上传（el-upload 自定义 http-request）：成功后把后端返回的相对 URL 回填 form.image
// 接口：POST /admin/api/upload（category=banner，返回 /uploads/banner/{uuid}.ext）
async function handleUpload(options) {
  try {
    const url = await uploadImage(options.file, 'banner')
    form.image = url
    ElMessage.success('图片上传成功')
    options.onSuccess(url)
  } catch (e) {
    ElMessage.error(e.message || '图片上传失败')
    options.onError(e)
  }
}

function beforeUpload(file) {
  const okTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!okTypes.includes(file.type)) {
    ElMessage.error('仅支持 jpg/png/gif/webp 图片')
    return false
  }
  if (file.size / 1024 / 1024 > 5) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除运营位「${row.title}」吗？`, '提示', { type: 'warning' })
  await deleteBanner(row.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(() => {
  load()
  onWS('catalog_changed', load)
})
</script>

<template>
  <div>
    <el-card>
      <div class="toolbar">
        <el-button type="success" @click="openCreate">新增运营位</el-button>
      </div>
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="位置" width="90">
          <template #default="{ row }">{{ row.position === 'hero' ? '首页横幅' : '主题' }}</template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="140" />
        <el-table-column prop="sub_title" label="副标题" min-width="140" />
        <el-table-column label="图片" min-width="120">
          <template #default="{ row }">
            <el-image :src="row.image" style="width: 60px; height: 40px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="link_type" label="跳转类型" width="100" />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑运营位' : '新增运营位'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="位置">
          <el-radio-group v-model="form.position">
            <el-radio value="hero">首页横幅</el-radio>
            <el-radio value="theme">主题</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.sub_title" />
        </el-form-item>
        <el-form-item label="图片" prop="image">
          <el-upload
            accept="image/*"
            :show-file-list="false"
            :http-request="handleUpload"
            :before-upload="beforeUpload"
            class="banner-upload"
          >
            <div class="upload-trigger">
              <el-image v-if="form.image" :src="form.image" fit="cover" class="upload-preview">
                <template #error>
                  <div class="upload-empty">
                    <el-icon :size="24"><Plus /></el-icon>
                    <span>加载失败</span>
                  </div>
                </template>
              </el-image>
              <div v-else class="upload-empty">
                <el-icon :size="24"><Plus /></el-icon>
                <span>上传图片</span>
              </div>
              <div v-if="form.image" class="upload-mask">
                <el-icon><RefreshRight /></el-icon>
                <span>更换图片</span>
              </div>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="跳转类型">
          <el-select v-model="form.link_type" style="width: 100%">
            <el-option label="无" value="none" />
            <el-option label="商品" value="product" />
            <el-option label="分类" value="category" />
            <el-option label="页面" value="page" />
          </el-select>
        </el-form-item>
        <el-form-item label="跳转值">
          <el-input v-model="form.link_value" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" style="width: 100%" />
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
  </div>
</template>

<style scoped>
.toolbar {
  margin-bottom: 16px;
}
.banner-upload {
  display: inline-block;
}
.upload-trigger {
  position: relative;
  width: 320px;
  height: 160px;
  overflow: hidden;
  border-radius: 8px;
  border: 1px dashed #d0d0d0;
  background: #fafafa;
  cursor: pointer;
  transition: border-color 0.2s;
}
.upload-trigger:hover {
  border-color: var(--el-color-primary);
}
.upload-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.upload-preview {
  width: 100%;
  height: 100%;
}
.upload-mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #fff;
  font-size: 12px;
  background: rgba(0, 0, 0, 0.45);
  opacity: 0;
  transition: opacity 0.2s;
}
.upload-trigger:hover .upload-mask {
  opacity: 1;
}
</style>
