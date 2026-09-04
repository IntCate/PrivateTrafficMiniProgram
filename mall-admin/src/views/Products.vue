<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createProduct, deleteProduct, listCategories, listProducts, updateProduct, updateProductStatus } from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ page: 1, pageSize: 10, keyword: '' })
const categories = ref([])

const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const form = reactive({
  product_no: '',
  category_id: null,
  brand: '',
  name: '',
  sub_title: '',
  price: 0,
  original_price: null,
  main_image: '',
  images: [],
  detail_html: '',
  stock: 0,
  tags: [],
  shipping_from: '',
  is_free_shipping: true,
  status: 1,
})

const rules = {
  product_no: [{ required: true, message: '请输入商品编号', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  main_image: [{ required: true, message: '请输入主图地址', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const data = await listProducts(query)
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

function handleSearch() {
  query.page = 1
  load()
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    product_no: '',
    category_id: null,
    brand: '',
    name: '',
    sub_title: '',
    price: 0,
    original_price: null,
    main_image: '',
    images: [],
    detail_html: '',
    stock: 0,
    tags: [],
    shipping_from: '',
    is_free_shipping: true,
    status: 1,
  })
  dialogVisible.value = true
}

async function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    product_no: row.product_no,
    category_id: row.category_id,
    brand: row.brand || '',
    name: row.name,
    sub_title: row.sub_title || '',
    price: Number(row.price),
    original_price: row.original_price != null ? Number(row.original_price) : null,
    main_image: row.main_image || '',
    images: row.images || [],
    detail_html: row.detail_html || '',
    stock: row.stock,
    tags: row.tags || [],
    shipping_from: row.shipping_from || '',
    is_free_shipping: row.is_free_shipping,
    status: row.status,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = { ...form }
  if (editingId.value) {
    await updateProduct(editingId.value, payload)
    ElMessage.success('更新成功')
  } else {
    await createProduct(payload)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
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
})
</script>

<template>
  <div>
    <el-card>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="搜索商品名称/编号" clearable style="width: 240px" @keyup.enter="handleSearch" @clear="handleSearch" />
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button type="success" @click="openCreate">新增商品</el-button>
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
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑商品' : '新增商品'" width="640px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="商品编号" prop="product_no">
          <el-input v-model="form.product_no" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="form.category_id" placeholder="请选择分类" style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌">
          <el-input v-model="form.brand" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.sub_title" />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="原价">
          <el-input-number v-model="form.original_price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="主图" prop="main_image">
          <el-input v-model="form.main_image" placeholder="图片 URL" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="form.stock" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="form.tags" multiple allow-create filterable default-first-option placeholder="输入后回车添加" style="width: 100%" />
        </el-form-item>
        <el-form-item label="发货地">
          <el-input v-model="form.shipping_from" />
        </el-form-item>
        <el-form-item label="包邮">
          <el-switch v-model="form.is_free_shipping" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">上架</el-radio>
            <el-radio :value="0">下架</el-radio>
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
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
