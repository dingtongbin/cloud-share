<template>
  <div>
    <!-- 创建用户 -->
    <el-card class="mb-4">
      <template #header>创建用户</template>
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px" inline>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item label="存储空间">
          <el-input-number v-model="createForm.storage_limit" :min="1" :step="1024" />
          <span class="text-muted" style="margin-left: 4px;">MB</span>
        </el-form-item>
        <el-form-item label="限速">
          <el-input-number v-model="createForm.speed_limit" :min="0" :step="100" />
          <span class="text-muted" style="margin-left: 4px;">KB/s (0=不限速)</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleCreate">创建</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card>
      <template #header>用户列表</template>
      <el-table :data="users" style="width: 100%">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="存储空间" width="180">
          <template #default="{ row }">
            <div>{{ formatSize(row.used_space) }} / {{ formatSize(row.quota) }}</div>
            <el-progress :percentage="getStoragePercent(row)" :stroke-width="6" />
          </template>
        </el-table-column>
        <el-table-column label="限速" width="100">
          <template #default="{ row }">{{ row.speed_limit ? `${row.speed_limit} KB/s` : '不限速' }}</template>
        </el-table-column>
        <el-table-column prop="file_count" label="文件数" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="editUser(row)">编辑</el-button>
            <el-button text size="small" @click="changePwdUser(row)">改密码</el-button>
            <el-button text size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggleActive(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button text size="small" type="danger" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="showEdit" title="编辑用户" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="存储空间">
          <el-input-number v-model="editForm.storage_limit" :min="1" :step="1024" />
          <span class="text-muted" style="margin-left: 4px;">MB</span>
        </el-form-item>
        <el-form-item label="限速">
          <el-input-number v-model="editForm.speed_limit" :min="0" :step="100" />
          <span class="text-muted" style="margin-left: 4px;">KB/s</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 改密码对话框 -->
    <el-dialog v-model="showChangePwd" title="修改密码" width="400px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
          <div v-if="pwdForm.new_password" style="margin-top: 4px; font-size: 12px;">
            <span :style="{ color: pwdStrength.color }">密码强度: {{ pwdStrength.text }}</span>
            <span style="margin-left: 8px; color: #909399;">需8位以上，含大小写字母和数字</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePwd = false">取消</el-button>
        <el-button type="primary" @click="savePwd">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const users = ref([])
const createFormRef = ref()
const editingUserId = ref(null)
const changingPwdUserId = ref(null)

const createForm = reactive({
  username: '',
  password: '',
  email: '',
  storage_limit: 10240,
  speed_limit: 0,
})

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

const pwdStrength = computed(() => {
  const p = pwdForm.new_password
  if (!p) return { level: 0, text: '', color: '' }
  let score = 0
  if (p.length >= 8) score++
  if (p.length >= 12) score++
  if (/[a-z]/.test(p)) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^a-zA-Z0-9]/.test(p)) score++
  if (score <= 2) return { level: score, text: '弱', color: '#F56C6C' }
  if (score <= 4) return { level: score, text: '中', color: '#E6A23C' }
  return { level: score, text: '强', color: '#67C23A' }
})

const createRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, validator: validateStrongPassword, trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
}

const pwdRules = {
  new_password: [{ required: true, validator: validateStrongPassword, trigger: 'blur' }],
}

const pwdFormRef = ref()

const showEdit = ref(false)
const editForm = reactive({ email: '', storage_limit: 10240, speed_limit: 0 })

const showChangePwd = ref(false)
const pwdForm = reactive({ new_password: '' })

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0, size = bytes
  while (size >= 1024 && i < 4) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

const formatTime = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

const getStoragePercent = (user) => {
  const limit = user.quota || 0
  if (limit === 0) return 0
  return Math.min(100, Math.round(((user.used_space || 0) / limit) * 100))
}

const loadUsers = async () => {
  users.value = await request.get('/admin/users')
}

const handleCreate = async () => {
  if (!createFormRef.value) return
  await createFormRef.value.validate()
  // storage_limit 是 MB，转换为字节传给后端
  await request.post('/admin/users', {
    username: createForm.username,
    password: createForm.password,
    email: createForm.email,
    quota: createForm.storage_limit * 1024 * 1024,
    speed_limit: createForm.speed_limit,
  })
  ElMessage.success('用户创建成功')
  createForm.username = ''
  createForm.password = ''
  createForm.email = ''
  createForm.storage_limit = 10240
  createForm.speed_limit = 0
  loadUsers()
}

const editUser = (user) => {
  editingUserId.value = user.id
  editForm.email = user.email
  // quota 是字节，转换为 MB 显示
  editForm.storage_limit = Math.round((user.quota || 0) / (1024 * 1024))
  editForm.speed_limit = user.speed_limit || 0
  showEdit.value = true
}

const saveEdit = async () => {
  // storage_limit 是 MB，转换为字节传给后端
  await request.put(`/admin/users/${editingUserId.value}`, {
    email: editForm.email,
    quota: editForm.storage_limit * 1024 * 1024,
    speed_limit: editForm.speed_limit,
  })
  ElMessage.success('更新成功')
  showEdit.value = false
  loadUsers()
}

const changePwdUser = (user) => {
  changingPwdUserId.value = user.id
  pwdForm.new_password = ''
  showChangePwd.value = true
}

const savePwd = async () => {
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate()
  await request.post(`/admin/users/${changingPwdUserId.value}/change-password`, pwdForm)
  ElMessage.success('密码已修改')
  showChangePwd.value = false
}

const toggleActive = async (user) => {
  const action = user.is_active ? '禁用' : '启用'
  await ElMessageBox.confirm(`确定${action}用户 ${user.username}？`, '确认')
  await request.put(`/admin/users/${user.id}`, { is_active: !user.is_active })
  ElMessage.success(`已${action}`)
  loadUsers()
}

const deleteUser = async (user) => {
  await ElMessageBox.confirm(`确定删除用户 ${user.username}？此操作不可恢复！`, '警告', { type: 'warning' })
  await request.delete(`/admin/users/${user.id}`)
  ElMessage.success('用户已删除')
  loadUsers()
}

onMounted(loadUsers)
</script>
