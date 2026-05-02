<template>
  <div>
    <el-card class="mb-4">
      <template #header>个人信息</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{ user?.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ user?.email }}</el-descriptions-item>
        <el-descriptions-item label="存储空间">
          <div>
            <span>{{ formatSize(user?.used_space || 0) }} / {{ formatSize(user?.quota || 10 * 1024 * 1024 * 1024) }}</span>
            <el-progress :percentage="storagePercent" :stroke-width="8" class="mt-2" />
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="速度限制">
          {{ user?.speed_limit ? `${user.speed_limit} KB/s` : '不限速' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card>
      <template #header>修改密码</template>
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px" style="max-width: 500px;">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="pwdForm.confirm" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="changePwd">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const user = ref(null)
const pwdFormRef = ref()

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== pwdForm.new_password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}


const validateStrongPassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入密码'))
  } else if (value.length < 8) {
    callback(new Error('密码至少8位'))
  } else if (!/[a-z]/.test(value)) {
    callback(new Error('密码需包含小写字母'))
  } else if (!/[A-Z]/.test(value)) {
    callback(new Error('密码需包含大写字母'))
  } else if (!/[0-9]/.test(value)) {
    callback(new Error('密码需包含数字'))
  } else {
    callback()
  }
}

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [{ required: true, validator: validateStrongPassword, trigger: 'blur' }],
  confirm: [{ required: true, validator: validateConfirm, trigger: 'blur' }],
}

const storagePercent = computed(() => {
  if (!user.value) return 0
  const limit = user.value.quota || 10 * 1024 * 1024 * 1024
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
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate()
  await request.post('/auth/change-password', {
    old_password: pwdForm.old_password,
    new_password: pwdForm.new_password,
  })
  ElMessage.success('密码修改成功')
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm = ''
}

onMounted(loadUser)
</script>
