<template>
  <div class="login-wrapper">
    <div class="login-box">
      <div class="login-header">
        <img src="/logo.svg" alt="Cloud Driver" class="login-logo" />
        <h2>Cloud Driver</h2>
        <p class="text-muted">个人网盘系统</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" class="w-full" :loading="loading" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  
  loading.value = true
  try {
    const res = await request.post('/auth/login', form)
    localStorage.setItem('token', res.access_token)
    
    // 获取用户信息
    const user = await request.get('/auth/me')
    localStorage.setItem('user', JSON.stringify(user))
    
    ElMessage.success('登录成功')
    router.push(user.is_admin ? '/admin/users' : '/files')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  background-image:
    radial-gradient(at 20% 80%, rgba(79, 142, 247, 0.08) 0px, transparent 50%),
    radial-gradient(at 80% 20%, rgba(124, 92, 252, 0.06) 0px, transparent 50%),
    radial-gradient(at 50% 50%, rgba(79, 142, 247, 0.04) 0px, transparent 70%);
}

.login-box {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 40px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  width: 72px;
  height: 72px;
  margin-bottom: 12px;
}

.login-header h2 {
  font-size: 24px;
  color: var(--text-primary);
  margin-bottom: 4px;
}
</style>
