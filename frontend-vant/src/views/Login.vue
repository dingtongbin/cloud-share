<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <div style="font-size: 48px; margin-bottom: 8px;">☁️</div>
        <h2>Cloud Driver</h2>
        <p class="text-muted text-sm">个人网盘系统</p>
      </div>
      <van-form @submit="handleLogin">
        <van-cell-group inset>
          <van-field v-model="form.username" name="username" label="用户名" placeholder="请输入用户名"
            :rules="[{ required: true, message: '请输入用户名' }]" />
          <van-field v-model="form.password" type="password" name="password" label="密码" placeholder="请输入密码"
            :rules="[{ required: true, message: '请输入密码' }]" />
        </van-cell-group>
        <div style="padding: 16px;">
          <van-button round block type="primary" native-type="submit" :loading="loading">登 录</van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import request from '../utils/request'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const handleLogin = async () => {
  loading.value = true
  try {
    const res = await request.post('/auth/login', form)
    localStorage.setItem('token', res.access_token)
    const user = await request.get('/auth/me')
    localStorage.setItem('user', JSON.stringify(user))
    showToast('登录成功')
    router.push(user.is_admin ? '/admin/users' : '/files')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg-primary);
  background-image: radial-gradient(at 20% 80%, rgba(25, 137, 250, 0.08) 0px, transparent 50%),
    radial-gradient(at 80% 20%, rgba(124, 92, 252, 0.06) 0px, transparent 50%);
  padding: 20px;
}
.login-box { background: var(--bg-secondary); border-radius: 16px; padding: 32px 20px; width: 100%; max-width: 380px; box-shadow: 0 8px 32px var(--shadow-color); }
.login-header { text-align: center; margin-bottom: 24px; }
.login-header h2 { font-size: 22px; color: var(--text-primary); margin-bottom: 4px; }
</style>
