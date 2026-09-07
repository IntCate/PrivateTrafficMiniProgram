<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref, watch } from 'vue'

import { createProduct, createProductSku, deleteProduct, deleteProductSku, getProduct, listCategories, listProducts, updateProduct, updateProductSku, updateProductStatus } from '@/api'
import { onWS } from '@/utils/ws'
import ProductForm from './ProductForm.vue'

const props = defineProps({
  // 选中的分类 id（null 表示全部商品）
  categoryId: { type: [Number, null], default: null },
})

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ page: 1, pageSize: 10, keyword: '' })
const categories = ref([])

const dialogVisible = ref(false)
const editing = ref(null)

async function load() {
  loading.value = true
  try {
    const data = await listProducts({
      page: query.page,
      pageSize: query.pageSize,
      keyword: query.keyword || undefined,
      category_id: props.categoryId || undefined,
    })
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  const data = await listCategories()
  categories.value = data.list
}

watch(
  () => props.categoryId,
  () => {
    query.page = 1
    load()
  }
)

function handleSearch() {
  query.page = 1
  load()
}

function openCreate() {
  editing.value = null
  dialogVisible.value = true
}

async function openEdit(row) {
  editing.value = await getProduct(row.id)
  dialogVisible.value = true
}

async function handleSaved(payload) {
  const { skuList, originalSkuIds, ...productData } = payload
  let productId
  if (editing.value) {
    await updateProduct(editing.value.id, productData)
    productId = editing.value.id
    ElMessage.success('更新成功')
  } else {
    const created = await createProduct(productData)
    productId = created.id
    ElMessage.success('创建成功')
  }
  await saveSkus(productId, skuList, originalSkuIds)
  dialogVisible.value = false
  load()
}

// 保存 SKU：删除被移除的，新增/更新其余
async function saveSkus(productId, skuList, originalSkuIds) {
  const currentIds = (skuList || []).filter((s) => s.id).map((s) => s.id)
  const removedIds = (originalSkuIds || []).filter((id) => !currentIds.includes(id))
  for (const id of removedIds) {
    await deleteProductSku(productId, id)
  }
  for (const s of skuList || []) {
    const payload = {
      sku_code: s.sku_code,
      attrs: s.attrs,
      sku_text: s.sku_text,
      price: s.price,
      stock: s.stock,
      status: s.status,
    }
    if (s.id) {
      await updateProductSku(productId, s.id, payload)
    } else {
      await createProductSku(productId, payload)
    }
  }
}

async function handleStatus(row) {
  await updateProductStatus(row.id, { status: row.status === 1 ? 0 : 1 })
  ElMessage.success('操作成功')
  load()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除商品「${row.name}」吗？`, '提示', { type: 'warning' })
  await deleteProduct(row.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(() => {
  load()
  loadCategories()
  onWS('catalog_changed', () => {
    loadCategories()
    load()
  })
})
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="搜索商品名称/编号" clearable style="width: 240px" @keyup.enter="handleSearch" @clear="handleSearch" />
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button type="success" @click="openCreate">新增商品</el-button>
      <span v-if="categoryId" class="scope-tip">当前分类下的商品</span>
      <span v-else class="scope-tip">全部商品</span>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="product_no" label="编号" width="120" />
      <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
      <el-table-column label="价格" width="100">
        <template #default="{ row }">¥{{ row.price }}</template>
      </el-table-column>
      <el-table-column prop="stock" label="库存" width="80" />
      <el-table-column prop="sales" label="销量" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '上架' : '下架' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" :type="row.status === 1 ? 'warning' : 'success'" @click="handleStatus(row)">
            {{ row.status === 1 ? '下架' : '上架' }}
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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

    <ProductForm
      v-model="dialogVisible"
      :categories="categories"
      :preset-category-id="categoryId"
      :editing="editing"
      @saved="handleSaved"
    />
  </el-card>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.scope-tip {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>