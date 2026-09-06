<script setup>
import { ElMessage } from 'element-plus'
import { reactive, ref, watch } from 'vue'
import { Plus, RefreshRight } from '@element-plus/icons-vue'

import { uploadImage } from '@/api'

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
const specEntries = ref([])
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
  spec: {},
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

watch(
  () => props.modelValue,
  (v) => {
    if (v) reset()
  }
)

function reset() {
  const e = props.editing
  specEntries.value = Object.entries(e && e.spec ? e.spec : {}).map(([key, value]) => ({ key, value: String(value) }))
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
          spec: e.spec || {},
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
          spec: {},
          stock: 0,
          tags: [],
          shipping_from: '',
          is_free_shipping: true,
          status: 1,
        }
  )
}

async function submit() {
  await formRef.value.validate()
  const spec = {}
  specEntries.value.forEach((entry) => {
    if (entry.key && entry.value !== '') spec[entry.key] = entry.value
  })
  emit('saved', { ...form, spec })
}

function addSpec() {
  specEntries.value.push({ key: '', value: '' })
}

function removeSpec(index) {
  specEntries.value.splice(index, 1)
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
      <el-form-item label="规格参数">
        <div class="spec-editor">
          <div v-for="(entry, si) in specEntries" :key="si" class="spec-item">
            <el-input v-model="entry.key" placeholder="参数名" style="width: 40%" />
            <el-input v-model="entry.value" placeholder="参数值" style="width: 40%" />
            <el-button link type="danger" @click="removeSpec(si)">删除</el-button>
          </div>
          <el-button @click="addSpec">+ 添加参数</el-button>
        </div>
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
.spec-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.spec-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>