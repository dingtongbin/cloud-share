<template>
  <div>
    <!-- 个人信息 -->
    <van-cell-group inset title="个人信息" style="margin-bottom: 12px;">
      <van-cell title="用户名" :value="user?.username" />
      <van-cell title="邮箱" :value="user?.email || '-'" />
      <van-cell title="存储空间">
        <template #value>
          <span>{{ formatSize(user?.used_space || 0) }} / {{ formatSize(user?.quota || 0) }}</span>
          <van-progress :percentage="storagePercent" :show-pivot="false" style="margin-top: 4px;" />
        </template>
      </van-cell>
      <van-cell title="速度限制" :value="user?.speed_limit ? `${user.speed_limit} KB/s` : '不限速'" />
    </van-cell-group>

    <!-- 修改密码 -->
    <van-cell-group inset title="修改密码">
      <van-form @submit="changePwd">
        <van-field v-model="pwdForm.old_password" type="password" label="原密码" placeholder="请输入原密码"
          :rules="[{ required: true, message: '请输入原密码' }]" />
        <van-field v-model="pwdForm.new_password" type="password" label="新密码" placeholder="请输入新密码"
          :rules="[{ required: true, validator: validateStrongPassword, message: '密码需8位+大小写字母+数字' }]" />
        <van-field v-model="pwdForm.confirm" type="password" label="确认密码" placeholder="请再次输入新密码"
          :rules="[{ required: true, validator: validateConfirm, message: '两次密码不一致' }]" />
        <div style="padding: 16px;">
          <van-button round block type="primary" native-type="submit">修改密码</van-button>
        </div>
      </van-form>
    </van-cell-group>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { showToast } from 'vant'
import request from '../utils/request'

const user = ref(null)
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })

const validateStrongPassword = (val) => {
  if (!val) return false
  if (val.length < 8) return false
  if (!/[a-z]/.test(val)) return false
  if (!/[A-Z]/.test(val)) return false
  if (!/[0-9]/.test(val)) return false
  return true
}

const validateConfirm = (val) => val === pwdForm.new_password

const storagePercent = computed(() => {
  if (!user.value) return 0
  const limit = user.value.quota || 0
  if (limit === 0) return 0
  return Math.min(100, Math.round(((user.value.used_space || 0) / limit) * 100))
})

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0, size = bytes
  while (size >= 1024 && i < 4) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

const loadUser = async () => {
  try {
    const data = await request.get('/auth/me')
    user.value = data
    localStorage.setItem('user', JSON.stringify(data))
  } catch {}
}

const changePwd = async () => {
  await request.post('/auth/change-password', {
    old_password: pwdForm.old_password,
    new_password: pwdForm.new_password,
  })
  showToast('密码修改成功')
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm = ''
}

onMounted(loadUser)
</script>
