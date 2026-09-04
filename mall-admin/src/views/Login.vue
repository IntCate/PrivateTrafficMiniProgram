<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Shop, User, Lock } from '@element-plus/icons-vue'

import { login } from '@/api'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: 'admin',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const data = await login(form)
    userStore.setLogin(data.token, data.admin)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="brand-panel">
      <div class="brand-content">
        <div class="brand-logo">
          <el-icon><Shop /></el-icon>
        </div>
        <h1 class="brand-title">快乐购商城</h1>
        <p class="brand-subtitle">管理后台</p>
        <p class="brand-desc">高效管理商品、订单、会员与营销活动<br>一站式私域电商运营平台</p>
        <div class="brand-features">
          <div class="feature">
            <span class="feature-dot"></span>
            <span>实时数据概览</span>
          </div>
          <div class="feature">
            <span class="feature-dot"></span>
            <span>全链路订单管理</span>
          </div>
          <div class="feature">
            <span class="feature-dot"></span>
            <span>精细化会员运营</span>
          </div>
        </div>
      </div>
      <div class="brand-footer">© 2026 快乐购商城 · All Rights Reserved</div>
    </div>

    <div class="form-panel">
      <div class="form-card">
        <div class="form-header">
          <h2>欢迎回来</h2>
          <p>请登录您的管理账号</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @keyup.enter="handleLogin">
          <el-form-item label="账号" prop="username">
            <el-input v-model="form.username" placeholder="请输入账号" size="large">
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password size="large">
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-button type="primary" class="submit-btn" size="large" :loading="loading" @click="handleLogin">登 录</el-button>
        </el-form>

        <div class="form-tip">
          <span>默认账号：admin / Admin@123456</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
}

/* 左侧品牌区 */
.brand-panel {
  width: 45%;
  background: linear-gradient(160deg, #134e4a 0%, #0f766e 50%, #115e59 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 60px;
  color: #fff;
}
.brand-panel::before {
  content: '';
  position: absolute;
  top: -120px;
  right: -120px;
  width: 400px;
  height: 400px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 50%;
}
.brand-panel::after {
  content: '';
  position: absolute;
  bottom: -80px;
  left: -80px;
  width: 280px;
  height: 280px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 50%;
}
.brand-content {
  position: relative;
  z-index: 1;
  margin-top: 20%;
}
.brand-logo {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin-bottom: 28px;
}
.brand-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: 1px;
}
.brand-subtitle {
  font-size: 18px;
  opacity: 0.85;
  margin-bottom: 36px;
  font-weight: 300;
}
.brand-desc {
  font-size: 15px;
  line-height: 1.8;
  opacity: 0.75;
  margin-bottom: 40px;
}
.brand-features {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.feature {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  opacity: 0.85;
}
.feature-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #5eead4;
}
.brand-footer {
  position: relative;
  z-index: 1;
  font-size: 13px;
  opacity: 0.5;
}

/* 右侧表单区 */
.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  padding: 40px;
}
.form-card {
  width: 100%;
  max-width: 400px;
}
.form-header {
  margin-bottom: 36px;
}
.form-header h2 {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: 8px;
}
.form-header p {
  font-size: 14px;
  color: var(--text-3);
}
.submit-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  margin-top: 8px;
  background: linear-gradient(135deg, var(--primary), var(--primary-light)) !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
}
.submit-btn:hover {
  box-shadow: 0 6px 20px rgba(13, 148, 136, 0.4);
  transform: translateY(-1px);
}
.form-tip {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: var(--text-3);
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-2);
}
</style>
