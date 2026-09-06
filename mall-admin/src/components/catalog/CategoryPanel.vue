<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, FolderOpened, Search } from '@element-plus/icons-vue'

import { createCategory, deleteCategory, listCategories, updateCategory } from '@/api'
import { onWS } from '@/utils/ws'

const emit = defineEmits(['select'])

const loading = ref(false)
const treeData = ref([])
const selectedId = ref(null)
const search = ref('')

const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const form = reactive({ parent_id: 0, name: '', icon: '', sort: 0, status: 1 })
const rules = { name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try {
    const data = await listCategories()
    treeData.value = buildTree(data.list, 0)
  } finally {
    loading.value = false
  }
}

// 由扁平分类列表构建树（parent_id=0 为一级）
function buildTree(items, parentId) {
  return items
    .filter((i) => Number(i.parent_id) === Number(parentId))
    .sort((a, b) => Number(a.sort || 0) - Number(b.sort || 0))
    .map((i) => ({
      ...i,
      children: buildTree(items, i.id).length ? buildTree(items, i.id) : undefined,
    }))
}

// 关键词过滤：命中自身或其子分类时保留该节点（保留父级链路）
function filterByName(items, kw) {
  return items
    .map((node) => {
      const children = node.children ? filterByName(node.children, kw) : []
      const selfMatch = node.name.includes(kw)
      if (selfMatch || children.length) {
        return { ...node, children: children.length ? children : undefined }
      }
      return null
    })
    .filter(Boolean)
}

const filteredTree = computed(() => {
  const kw = search.value.trim()
  return kw ? filterByName(treeData.value, kw) : treeData.value
})

// 分类选择下拉的扁平选项（含缩进层级 + “顶级”项）
const categoryOptions = computed(() => {
  const rows = [{ id: 0, name: '— 顶级分类 —', depth: -1 }]
  const walk = (nodes, depth) => {
    for (const n of nodes) {
      rows.push({ id: n.id, name: n.name, depth })
      if (n.children) walk(n.children, depth + 1)
    }
  }
  walk(treeData.value, 0)
  return rows
})

function selectAll() {
  selectedId.value = null
  emit('select', null)
}

function selectNode(node) {
  selectedId.value = node.id
  emit('select', node.id)
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { parent_id: 0, name: '', icon: '', sort: 0, status: 1 })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, { parent_id: row.parent_id, name: row.name, icon: row.icon || '', sort: row.sort, status: row.status })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  if (editingId.value) {
    await updateCategory(editingId.value, form)
    ElMessage.success('更新成功')
  } else {
    await createCategory(form)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除分类「${row.name}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return // 用户取消
  }
  await deleteCategory(row.id) // 该分类下仍有商品时由后端返回 400，拦截器统一提示
  ElMessage.success('删除成功')
  if (selectedId.value === row.id) {
    selectedId.value = null
    emit('select', null)
  }
  load()
}

onMounted(() => {
  load()
  onWS('catalog_changed', load)
})
</script>

<template>
  <el-card shadow="never" class="category-panel">
    <template #header>
      <div class="panel-header">
        <div class="panel-title">
          <el-icon size="15"><FolderOpened /></el-icon>
          <span>分类管理</span>
        </div>
        <el-button type="primary" size="small" round @click="openCreate">新增分类</el-button>
      </div>
    </template>

    <el-input v-model="search" class="search-box" placeholder="搜索分类" clearable :prefix-icon="Search" />

    <div class="cat-list" v-loading="loading">
      <div
        :class="['cat-item', { active: selectedId === null }]"
        @click="selectAll"
      >
        <span class="cat-name">全部</span>
      </div>

      <el-tree
        v-if="filteredTree.length"
        :data="filteredTree"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        :expand-on-click-node="false"
        :default-expand-all="true"
        empty-text="暂无分类"
        class="cat-tree"
        @node-click="selectNode"
      >
        <template #default="{ data }">
          <div :class="['tree-node', { active: selectedId === data.id }]">
            <span class="tree-label">{{ data.name }}</span>
            <span class="tree-ops">
              <el-button size="small" circle text :icon="Edit" title="编辑" @click.stop="openEdit(data)" />
              <el-button size="small" circle text type="danger" :icon="Delete" title="删除" @click.stop="handleDelete(data)" />
            </span>
          </div>
        </template>
      </el-tree>
      <div v-else-if="!loading" class="cat-empty">暂无分类</div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分类' : '新增分类'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="父级">
          <el-select v-model="form.parent_id" style="width: 100%">
            <el-option v-for="o in categoryOptions" :key="o.id" :label="o.name" :value="o.id">
              <span :style="{ paddingLeft: `${Math.max(o.depth, 0) * 16}px` }">{{ o.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="图标 URL" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" style="width: 100%" />
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
  </el-card>
</template>

<style scoped>
.category-panel {
  border: none;
  box-shadow: none;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.search-box {
  margin-bottom: 10px;
}
.cat-list {
  max-height: calc(100vh - 260px);
  overflow-y: auto;
}
.cat-item,
.tree-node {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  height: 34px;
  margin: 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 400;
  color: var(--el-text-color-primary);
  transition: background-color 0.15s;
}
/* 「全部商品」留出与 el-tree 展开箭头(24px) + 节点内边距等宽的左占位，与一级分类文字对齐 */
.cat-item {
  padding: 0 30px;
}
.tree-node {
  flex: 1;
  min-width: 0;
  padding: 0 6px;
}
.cat-item:hover,
.tree-node:hover {
  background: var(--el-fill-color-light);
}
.cat-item.active,
.tree-node.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 500;
}
.cat-item.active::before,
.tree-node.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 16px;
  border-radius: 2px;
  background: var(--el-color-primary);
}
.cat-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tree-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tree-ops {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  margin-left: 6px;
}
.tree-ops :deep(.el-button.is-circle) {
  width: 24px;
  height: 24px;
  padding: 0;
}
.tree-ops :deep(.el-button .el-icon) {
  font-size: 13px;
}
.cat-empty {
  padding: 24px 0;
  text-align: center;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
}
/* 覆盖 el-tree 自身样式 */
.cat-tree :deep(.el-tree-node__content) {
  height: 34px;
}
</style>