<script setup>
import { ElMessage } from 'element-plus'
import { reactive, ref, watch } from 'vue'
import { Plus, RefreshRight } from '@element-plus/icons-vue'

import { listProductSkus, uploadImage } from '@/api'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  categories: { type: Array, default: () => [] },
  // 新增时预填的分类（null 表示自由选择）
  presetCategoryId: { type: [Number, null], default: null },
  // 编辑对象（编辑模式）；为空表示新增
  editing: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

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
  detail_blocks: [],
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
  main_image: [{ required: true, message: '请上传主图', trigger: 'blur' }],
}

// ---- SKU 管理（颜色/尺码等购买规格，由后台用户自定义）----
const skuLoading = ref(false)
const attrGroups = ref([]) // [{ name, values: [] }]
const skuList = ref([]) // [{ id?, attrs, sku_code, sku_text, price, stock, status }]
const originalSkuIds = ref([]) // 编辑时已存在的 SKU id，用于保存时识别删除

function addAttrGroup() {
  attrGroups.value.push({ name: '', values: [] })
}

function removeAttrGroup(index) {
  attrGroups.value.splice(index, 1)
}

function addAttrValue(gi) {
  attrGroups.value[gi].values.push('')
}

function removeAttrValue(gi, vi) {
  attrGroups.value[gi].values.splice(vi, 1)
}

// 根据属性组笛卡尔积生成 SKU 草稿（保留已填价格/库存）
function generateSkus() {
  const groups = attrGroups.value.filter((g) => g.name && g.values.some((v) => v))
  if (!groups.length) {
    ElMessage.warning('请先填写属性组名称和属性值')
    return
  }
  const combos = groups.reduce(
    (acc, g) => {
      const values = g.values.filter((v) => v)
      const next = []
      acc.forEach((prev) => {
        values.forEach((v) => next.push([...prev, { name: g.name, value: v }]))
      })
      return next
    },
    [[]]
  )
  const existing = new Map(skuList.value.map((s) => [s.attrs.map((a) => `${a.name}:${a.value}`).join('|'), s]))
  const merged = combos.map((attrs) => {
    const key = attrs.map((a) => `${a.name}:${a.value}`).join('|')
    const prev = existing.get(key)
    return {
      id: prev ? prev.id : undefined,
      attrs,
      sku_code: prev ? prev.sku_code : '',
      sku_text: prev ? prev.sku_text : attrs.map((a) => a.value).join(' / '),
      price: prev ? prev.price : 0,
      stock: prev ? prev.stock : 0,
      status: prev ? prev.status : 1,
    }
  })
  skuList.value = merged
}

function addSku() {
  skuList.value.push({
    id: undefined,
    attrs: [],
    sku_code: '',
    sku_text: '',
    price: 0,
    stock: 0,
    status: 1,
  })
}

function removeSku(index) {
  skuList.value.splice(index, 1)
}

async function loadSkus(productId) {
  if (!productId) {
    skuList.value = []
    originalSkuIds.value = []
    return
  }
  skuLoading.value = true
  try {
    const data = await listProductSkus(productId)
    skuList.value = (data.list || []).map((s) => ({
      id: s.id,
      attrs: s.attrs || [],
      sku_code: s.sku_code,
      sku_text: s.sku_text,
      price: Number(s.price),
      stock: s.stock,
      status: s.status,
    }))
    originalSkuIds.value = skuList.value.map((s) => s.id)
    // 由已有 SKU 反推属性组
    const groups = []
    skuList.value.forEach((s) => {
      s.attrs.forEach((a) => {
        let g = groups.find((x) => x.name === a.name)
        if (!g) {
          g = { name: a.name, values: [] }
          groups.push(g)
        }
        if (!g.values.includes(a.value)) g.values.push(a.value)
      })
    })
    attrGroups.value = groups
  } finally {
    skuLoading.value = false
  }
}

watch(
  () => props.modelValue,
  (v) => {
    if (v) reset()
  }
)

function reset() {
  const e = props.editing
  Object.assign(
    form,
    e
      ? {
          product_no: e.product_no,
          category_id: e.category_id,
          brand: e.brand || '',
          name: e.name,
          sub_title: e.sub_title || '',
          price: Number(e.price),
          original_price: e.original_price != null ? Number(e.original_price) : null,
          main_image: e.main_image || '',
          images: e.images || [],
          detail_blocks: e.detail_blocks || [],
          stock: e.stock,
          tags: e.tags || [],
          shipping_from: e.shipping_from || '',
          is_free_shipping: e.is_free_shipping,
          status: e.status,
        }
      : {
          product_no: '',
          category_id: props.presetCategoryId,
          brand: '',
          name: '',
          sub_title: '',
          price: 0,
          original_price: null,
          main_image: '',
          images: [],
          detail_blocks: [],
          stock: 0,
          tags: [],
          shipping_from: '',
          is_free_shipping: true,
          status: 1,
        }
  )
  loadSkus(e ? e.id : null)
}

async function submit() {
  await formRef.value.validate()
  emit('saved', {
    ...form,
    skuList: skuList.value,
    originalSkuIds: originalSkuIds.value,
  })
}

function close() {
  emit('update:modelValue', false)
}

// 主图上传（el-upload 自定义 http-request）：成功后把返回的相对 URL 回填 form.main_image
// 接口：POST /admin/api/upload（category=product，返回 /uploads/product/{uuid}.ext）
async function handleUpload(options) {
  try {
    const url = await uploadImage(options.file, 'product')
    form.main_image = url
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
  if (file.size / 1024 / 1024 > 10) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }
  return true
}

// 详情区块：添加文字段落
function addTextBlock() {
  form.detail_blocks.push({ type: 'text', content: '' })
}

// 详情区块：上传图片（成功后 push image 区块）
async function addImageBlock(options) {
  try {
    const url = await uploadImage(options.file, 'product')
    form.detail_blocks.push({ type: 'image', url })
    ElMessage.success('图片已添加')
    options.onSuccess(url)
  } catch (e) {
    ElMessage.error(e.message || '图片上传失败')
    options.onError(e)
  }
}

function removeBlock(index) {
  form.detail_blocks.splice(index, 1)
}

function moveBlock(index, dir) {
  const target = index + dir
  if (target < 0 || target >= form.detail_blocks.length) return
  const arr = form.detail_blocks
  ;[arr[index], arr[target]] = [arr[target], arr[index]]
}
</script>

<template>
  <el-dialog :model-value="modelValue" :title="editing ? '编辑商品' : '新增商品'" width="640px" @update:model-value="(v) => emit('update:modelValue', v)">
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
          <el-upload
            accept="image/*"
            :show-file-list="false"
            :http-request="handleUpload"
            :before-upload="beforeUpload"
            class="img-upload"
          >
            <div class="upload-trigger">
              <el-image v-if="form.main_image" :src="form.main_image" fit="cover" class="upload-preview">
                <template #error>
                  <div class="upload-empty">
                    <el-icon :size="22"><Plus /></el-icon>
                    <span>加载失败</span>
                  </div>
                </template>
              </el-image>
              <div v-else class="upload-empty">
                <el-icon :size="22"><Plus /></el-icon>
                <span>上传主图</span>
              </div>
              <div v-if="form.main_image" class="upload-mask">
                <el-icon><RefreshRight /></el-icon>
                <span>更换主图</span>
              </div>
            </div>
          </el-upload>
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
      <el-form-item label="详情内容">
        <div class="block-editor">
          <div v-for="(block, bi) in form.detail_blocks" :key="bi" class="block-item">
            <div class="block-toolbar">
              <span class="block-type">{{ block.type === 'text' ? '文字' : '图片' }}</span>
              <div class="block-actions">
                <el-button link size="small" :disabled="bi === 0" @click="moveBlock(bi, -1)">上移</el-button>
                <el-button link size="small" :disabled="bi === form.detail_blocks.length - 1" @click="moveBlock(bi, 1)">下移</el-button>
                <el-button link size="small" type="danger" @click="removeBlock(bi)">删除</el-button>
              </div>
            </div>
            <el-input
              v-if="block.type === 'text'"
              v-model="block.content"
              type="textarea"
              :rows="3"
              placeholder="输入文字段落"
            />
            <el-image v-else :src="block.url" fit="cover" class="block-image" />
          </div>
          <div class="block-add">
            <el-button @click="addTextBlock">+ 添加文字</el-button>
            <el-upload
              accept="image/*"
              :show-file-list="false"
              :http-request="addImageBlock"
              :before-upload="beforeUpload"
            >
              <el-button>+ 添加图片</el-button>
            </el-upload>
          </div>
        </div>
      </el-form-item>

      <el-form-item label="购买规格">
        <div class="sku-editor" v-loading="skuLoading">
          <div class="sku-tip">配置颜色/尺码等购买规格（SKU），由后台自定义属性组，前端购买时据此选择。</div>

          <div class="sku-groups">
            <div v-for="(group, gi) in attrGroups" :key="gi" class="sku-group">
              <div class="sku-group-head">
                <el-input v-model="group.name" placeholder="属性组名，如：颜色" style="width: 160px" />
                <el-button link type="danger" @click="removeAttrGroup(gi)">删除属性组</el-button>
              </div>
              <div class="sku-values">
                <div v-for="(val, vi) in group.values" :key="vi" class="sku-value">
                  <el-input v-model="group.values[vi]" placeholder="属性值，如：黑色" style="width: 160px" />
                  <el-button link type="danger" @click="removeAttrValue(gi, vi)">删除</el-button>
                </div>
                <el-button size="small" @click="addAttrValue(gi)">+ 添加属性值</el-button>
              </div>
            </div>
            <el-button @click="addAttrGroup">+ 添加属性组</el-button>
          </div>

          <div class="sku-generate">
            <el-button type="primary" plain @click="generateSkus">生成 SKU 组合</el-button>
            <el-button @click="addSku">+ 手动添加 SKU</el-button>
          </div>

          <el-table v-if="skuList.length" :data="skuList" border size="small" class="sku-table">
            <el-table-column label="规格" min-width="160">
              <template #default="{ row }">
                <el-input v-model="row.sku_text" placeholder="规格文案，如：黑色 / 42" />
              </template>
            </el-table-column>
            <el-table-column label="SKU 编码" width="150">
              <template #default="{ row }">
                <el-input v-model="row.sku_code" placeholder="如：P001-B-42" />
              </template>
            </el-table-column>
            <el-table-column label="价格" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.price" :min="0" :precision="2" :controls="false" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="库存" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.stock" :min="0" :controls="false" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-switch v-model="row.status" :active-value="1" :inactive-value="0" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70">
              <template #default="{ $index }">
                <el-button link type="danger" @click="removeSku($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-else class="sku-empty">暂无 SKU，可先添加属性组后「生成 SKU 组合」</div>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.img-upload {
  display: inline-block;
}
.upload-trigger {
  position: relative;
  width: 140px;
  height: 140px;
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
.block-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.block-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 8px;
  background: #fafafa;
}
.block-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.block-type {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.block-actions {
  display: flex;
  align-items: center;
}
.block-image {
  width: 100%;
  max-height: 200px;
  border-radius: 4px;
}
.block-add {
  display: flex;
  gap: 10px;
}
.sku-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sku-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.sku-groups {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.sku-group {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 10px;
  background: #fafafa;
}
.sku-group-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.sku-values {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.sku-value {
  display: flex;
  align-items: center;
  gap: 4px;
}
.sku-generate {
  display: flex;
  gap: 10px;
}
.sku-table {
  width: 100%;
}
.sku-empty {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  border: 1px dashed #e4e7ed;
  border-radius: 6px;
}
</style>