<template>
  <div>
    <!-- 创建用户 -->
    <van-cell-group inset title="创建用户" style="margin-bottom: 12px;">
      <van-form @submit="handleCreate">
        <van-field v-model="createForm.username" label="用户名" placeholder="用户名"
          :rules="[{ required: true, message: '请输入用户名' }]" />
        <van-field v-model="createForm.password" type="password" label="密码" placeholder="密码"
          :rules="[{ required: true, validator: validateStrongPassword, message: '需8位+大小写字母+数字' }]" />
        <van-field v-model="createForm.email" label="邮箱" placeholder="邮箱"
          :rules="[{ required: true, message: '请输入邮箱' }]" />
        <van-field label="存储空间(MB)">
          <template #input>
            <van-stepper v-model="createForm.storage_limit" :min="1" :step="1024" />
          </template>
        </van-field>
        <van-field label="限速(KB/s)">
          <template #input>
            <van-stepper v-model="createForm.speed_limit" :min="0" :step="100" />
            <span class="text-muted text-xs ml-2">0=不限速</span>
          </template>
        </van-field>
        <div style="padding: 16px;">
          <van-button round block type="primary" native-type="submit">创建</van-button>
        </div>
      </van-form>
    </van-cell-group>

    <!-- 用户列表 -->
    <van-cell-group inset title="用户列表">
      <van-cell v-for="user in users" :key="user.id" :title="user.username" :label="userDesc(user)" is-link @click="showUserActions(user)">
        <template #value>
          <van-tag :type="user.is_active ? 'success' : 'danger'">{{ user.is_active ? '启用' : '禁用' }}</van-tag>
        </template>
      </van-cell>
    </van-cell-group>

    <van-empty v-if="users.length === 0" description="暂无用户" />

    <!-- 操作面板 -->
    <van-action-sheet v-model:show="showActions" :actions="userActions" cancel-text="取消" @select="onUserAction" />

    <!-- 编辑用户 -->
    <van-popup v-model:show="showEdit" position="bottom" :style="{ maxHeight: '70vh' }" round>
      <div class="popup-content">
        <div class="popup-title">编辑用户</div>
        <van-cell-group inset>
          <van-field v-model="editForm.email" label="邮箱" />
          <van-field label="存储空间(MB)">
            <template #input>
              <van-stepper v-model="editForm.storage_limit" :min="1" :step="1024" />
            </template>
          </van-field>
          <van-field label="限速(KB/s)">
            <template #input>
              <van-stepper v-model="editForm.speed_limit" :min="0" :step="100" />
            </template>
          </van-field>
        </van-cell-group>
        <div style="padding: 16px;">
          <van-button round block type="primary" @click="saveEdit">保存</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 修改密码 -->
    <van-dialog v-model:show="showChangePwd" title="修改密码" show-cancel-button @confirm="savePwd">
      <div style="padding: 16px;">
        <van-field v-model="pwdForm.new_password" type="password" label="新密码" placeholder="新密码" />
        <div v-if="pwdForm.new_password" class="text-xs mt-2" :style="{ color: pwdStrength.color }">
          密码强度: {{ pwdStrength.text }}
          <span style="color: #909399; margin-left: 8px;">需8位+大小写字母+数字</span>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import request from '../../utils/request'

const users = ref([])
const showActions = ref(false)
const showEdit = ref(false)
const showChangePwd = ref(false)
const selectedUser = ref(null)
const editingUserId = ref(null)
const changingPwdUserId = ref(null)

const createForm = reactive({ username: '', password: '', email: '', storage_limit: 10240, speed_limit: 0 })
const editForm = reactive({ email: '', storage_limit: 10240, speed_limit: 0 })
const pwdForm = reactive({ new_password: '' })

const userActions = [
  { name: '编辑', value: 'edit' },
  { name: '改密码', value: 'pwd' },
  { name: '切换状态', value: 'toggle' },
  { name: '删除', color: '#ee0a24', value: 'delete' },
]

const validateStrongPassword = (val) => {
  if (!val || val.length < 8) return false
  if (!/[a-z]/.test(val)) return false
  if (!/[A-Z]/.test(val)) return false
  if (!/[0-9]/.test(val)) return false
  return true
}

const pwdStrength = computed(() => {
  const p = pwdForm.new_password
  if (!p) return { text: '', color: '' }
  let score = 0
  if (p.length >= 8) score++
  if (p.length >= 12) score++
  if (/[a-z]/.test(p)) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^a-zA-Z0-9]/.test(p)) score++
  if (score <= 2) return { text: '弱', color: '#F56C6C' }
  if (score <= 4) return { text: '中', color: '#E6A23C' }
  return { text: '强', color: '#67C23A' }
})

const userDesc = (user) => {
  const size = (bytes) => {
    if (!bytes) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let i = 0, s = bytes
    while (s >= 1024 && i < 4) { s /= 1024; i++ }
    return `${s.toFixed(1)} ${units[i]}`
  }
  return `${size(user.used_space)} / ${size(user.quota)} · ${user.file_count || 0}文件`
}

const loadUsers = async () => { users.value = await request.get('/admin/users') }

const handleCreate = async () => {
  await request.post('/admin/users', {
    username: createForm.username,
    password: createForm.password,
    email: createForm.email,
    quota: createForm.storage_limit * 1024 * 1024,
    speed_limit: createForm.speed_limit,
  })
  showToast('用户创建成功')
  Object.assign(createForm, { username: '', password: '', email: '', storage_limit: 10240, speed_limit: 0 })
  loadUsers()
}

const showUserActions = (user) => {
  selectedUser.value = user
  userActions[2].name = user.is_active ? '禁用' : '启用'
  showActions.value = true
}

const onUserAction = async (action) => {
  showActions.value = false
  const user = selectedUser.value
  switch (action.value) {
    case 'edit':
      editingUserId.value = user.id
      editForm.email = user.email
      editForm.storage_limit = Math.round((user.quota || 0) / (1024 * 1024))
      editForm.speed_limit = user.speed_limit || 0
      showEdit.value = true
      break
    case 'pwd':
      changingPwdUserId.value = user.id
      pwdForm.new_password = ''
      showChangePwd.value = true
      break
    case 'toggle': {
      const act = user.is_active ? '禁用' : '启用'
      showConfirmDialog({ title: '确认', message: `${act}用户 ${user.username}？` })
        .then(async () => {
          await request.put(`/admin/users/${user.id}`, { is_active: !user.is_active })
          showToast(`已${act}`)
          loadUsers()
        }).catch(() => {})
      break
    }
    case 'delete':
      showConfirmDialog({ title: '警告', message: `删除用户 ${user.username}？此操作不可恢复！` })
        .then(async () => {
          await request.delete(`/admin/users/${user.id}`)
          showToast('用户已删除')
          loadUsers()
        }).catch(() => {})
      break
  }
}

const saveEdit = async () => {
  await request.put(`/admin/users/${editingUserId.value}`, {
    email: editForm.email,
    quota: editForm.storage_limit * 1024 * 1024,
    speed_limit: editForm.speed_limit,
  })
  showToast('更新成功')
  showEdit.value = false
  loadUsers()
}

const savePwd = async () => {
  if (!validateStrongPassword(pwdForm.new_password)) {
    showToast('密码需8位+大小写字母+数字')
    return
  }
  await request.post(`/admin/users/${changingPwdUserId.value}/change-password`, pwdForm)
  showToast('密码已修改')
  showChangePwd.value = false
}

onMounted(loadUsers)
</script>

<style scoped>
.popup-content { max-height: 70vh; overflow: auto; }
.popup-title {
  padding: 16px; font-size: 16px; font-weight: 600; text-align: center;
  border-bottom: 1px solid var(--border-color); color: var(--text-primary);
}
</style>
