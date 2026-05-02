<template>
  <div class="share-access-page">
    <div class="share-card">
      <div style="font-size: 48px; margin-bottom: 16px;">📄</div>
      
      <template v-if="loading">
        <el-skeleton :rows="3" animated />
      </template>

      <template v-else-if="error">
        <el-result icon="error" :title="error" />
      </template>

      <template v-else-if="shareInfo">
        <h3 style="margin-bottom: 8px;">{{ shareInfo.file_name }}</h3>
        
        <div class="text-muted text-sm mb-4">
          <span v-if="shareInfo.file_size" class="mr-4">{{ formatSize(shareInfo.file_size) }}</span>
          <span>下载次数: {{ shareInfo.download_count }}{{ shareInfo.max_downloads ? `/${shareInfo.max_downloads}` : '' }}</span>
        </div>

        <!-- 密码输入 -->
        <template v-if="shareInfo.has_password && !verified">
          <el-form @submit.prevent="verifyPassword" class="mt-4">
            <el-input v-model="password" placeholder="请输入访问密码" type="password" show-password class="mb-2" />
            <el-button type="primary" class="w-full" @click="verifyPassword">验证</el-button>
          </el-form>
        </template>

        <!-- 下载按钮 -->
        <template v-else>
          <el-button type="primary" size="large" class="w-full" @click="download" :loading="downloading">
            下载文件
          </el-button>
        </template>

        <div class="text-xs text-muted mt-4" v-if="shareInfo.expire_at">
          过期时间: {{ formatTime(shareInfo.expire_at) }}
        </div>
      </template>

      <div class="mt-4">
        <a href="/login" style="color: var(--accent-color); font-size: 13px;">登录 Cloud Driver</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const route = useRoute()
const shareCode = route.params.id

const loading = ref(true)
const error = ref('')
const shareInfo = ref(null)
const password = ref('')
const verified = ref(false)
const downloading = ref(false)

const formatSize = (bytes) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0, size = bytes
  while (size >= 1024 && i < 3) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

const formatTime = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

const loadShareInfo = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/shares/access/${shareCode}`)
    shareInfo.value = res.data
    if (!res.data.has_password) {
      verified.value = true
    }
  } catch (err) {
    if (err.response?.status === 410) {
      error.value = err.response.data.detail || '分享已失效'
    } else {
      error.value = '分享链接不存在或已失效'
    }
  } finally {
    loading.value = false
  }
}

const verifyPassword = async () => {
  try {
    await axios.post(`/api/shares/verify/${shareCode}`, { password: password.value })
    verified.value = true
    ElMessage.success('密码验证成功')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '密码错误')
  }
}

const download = async () => {
  downloading.value = true
  try {
    const params = {}
    if (shareInfo.value.has_password) {
      params.password = password.value
    }
    const res = await axios.get(`/api/shares/download/${shareCode}`, {
      params,
      responseType: 'blob',
    })
    
    // 获取文件名
    const disposition = res.headers['content-disposition']
    let filename = 'download'
    if (disposition) {
      const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match) filename = decodeURIComponent(match[1].replace(/['"]/g, ''))
    }
    
    const blob = new Blob([res.data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('下载成功')
    // 刷新下载计数
    loadShareInfo()
  } catch (err) {
    ElMessage.error('下载失败')
  } finally {
    downloading.value = false
  }
}

onMounted(loadShareInfo)
</script>

<style scoped>
.share-access-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.share-card {
  background: var(--bg-secondary, #fff);
  border-radius: 16px;
  padding: 40px;
  width: 450px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}
</style>
