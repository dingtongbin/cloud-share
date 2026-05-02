<template>
  <div class="share-page">
    <!-- 加载态 -->
    <div v-if="loading" class="share-card">
      <van-loading size="24px" vertical>加载中...</van-loading>
    </div>

    <!-- 错误态 -->
    <div v-else-if="error" class="share-card">
      <van-empty :description="error">
        <template #image>
          <div style="font-size: 48px;">🔗</div>
        </template>
      </van-empty>
    </div>

    <!-- 密码验证 -->
    <div v-else-if="shareInfo && shareInfo.has_password && !verified" class="share-card">
      <div class="share-icon">🔒</div>
      <h3 class="share-title">此分享需要密码</h3>
      <van-field
        v-model="password"
        type="password"
        placeholder="请输入下载密码"
        class="password-input"
        @keyup.enter="verifyPassword"
      />
      <van-button
        round
        block
        type="primary"
        @click="verifyPassword"
        :loading="verifying"
        class="verify-btn"
      >
        验证密码
      </van-button>
    </div>

    <!-- 下载页 -->
    <div v-else-if="shareInfo" class="share-card download-card">
      <!-- 留言区域 -->
      <div v-if="shareInfo.message" class="message-block">
        <div class="message-header">
          <van-icon name="comment-o" size="16" />
          <span>分享者说</span>
        </div>
        <div class="message-body">{{ shareInfo.message }}</div>
      </div>

      <!-- 文件信息 -->
      <div class="file-section">
        <div class="file-icon-large">{{ getFileIcon(shareInfo.file_name) }}</div>
        <div class="file-info">
          <div class="file-name">{{ shareInfo.file_name }}</div>
          <div class="file-meta">
            <span v-if="shareInfo.file_size">{{ formatSize(shareInfo.file_size) }}</span>
            <span>下载 {{ shareInfo.download_count }}{{ shareInfo.max_downloads ? '/' + shareInfo.max_downloads : '' }}</span>
          </div>
        </div>
      </div>

      <!-- 文件列表（仅一个文件，下载按钮） -->
      <div class="file-list">
        <div class="file-item">
          <div class="file-item-icon">{{ getFileIcon(shareInfo.file_name) }}</div>
          <div class="file-item-info">
            <div class="file-item-name">{{ shareInfo.file_name }}</div>
            <div class="file-item-size">{{ shareInfo.file_size ? formatSize(shareInfo.file_size) : '' }}</div>
          </div>
          <van-button
            size="small"
            type="primary"
            icon="down"
            :loading="downloading"
            @click="download"
          >
            下载
          </van-button>
        </div>
      </div>

      <!-- 底部信息 -->
      <div class="footer-info">
        <span v-if="shareInfo.expire_at">过期时间: {{ formatTime(shareInfo.expire_at) }}</span>
        <a href="/login" class="login-link">登录 Cloud Driver</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import axios from 'axios'

const route = useRoute()
const shareCode = route.params.id

const loading = ref(true)
const error = ref('')
const shareInfo = ref(null)
const password = ref('')
const verified = ref(false)
const verifying = ref(false)
const downloading = ref(false)

const getFileIcon = (name) => {
  if (!name) return '📄'
  const ext = name.split('.').pop().toLowerCase()
  const icons = {
    jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', webp: '🖼️', svg: '🖼️', bmp: '🖼️',
    mp4: '🎬', avi: '🎬', mkv: '🎬', mov: '🎬', webm: '🎬',
    mp3: '🎵', wav: '🎵', flac: '🎵', ogg: '🎵',
    pdf: '📕', doc: '📝', docx: '📝', txt: '📝', md: '📝',
    xls: '📊', xlsx: '📊', csv: '📊',
    ppt: '📽️', pptx: '📽️',
    zip: '📦', rar: '📦', '7z': '📦', tar: '📦', gz: '📦',
    js: '💻', ts: '💻', py: '💻', java: '💻', c: '💻', cpp: '💻', html: '💻', css: '💻', json: '💻',
    exe: '⚙️', sh: '⚙️', bat: '⚙️',
  }
  return icons[ext] || '📄'
}

const formatSize = (bytes) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0, size = bytes
  while (size >= 1024 && i < 3) { size /= 1024; i++ }
  return size.toFixed(1) + ' ' + units[i]
}

const formatTime = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

const loadShareInfo = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/shares/access/' + shareCode)
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
  if (!password.value) {
    showToast('请输入密码')
    return
  }
  verifying.value = true
  try {
    await axios.post('/api/shares/verify/' + shareCode, { password: password.value })
    verified.value = true
    showToast('密码验证成功')
  } catch (err) {
    showToast(err.response?.data?.detail || '密码错误')
  } finally {
    verifying.value = false
  }
}

const download = async () => {
  downloading.value = true
  try {
    const params = {}
    if (shareInfo.value.has_password) {
      params.password = password.value
    }
    const res = await axios.get('/api/shares/download/' + shareCode, {
      params,
      responseType: 'blob',
    })

    const disposition = res.headers['content-disposition']
    let filename = 'download'
    if (disposition) {
      const rfc5987 = disposition.match(/filename\*=utf-8''([^;\s]+)/i)
      if (rfc5987) {
        filename = decodeURIComponent(rfc5987[1])
      } else {
        const plain = disposition.match(/filename\s*=\s*"?([^";]+)"?/)
        if (plain) {
          filename = plain[1].trim()
        }
    }
      }

    const blob = new Blob([res.data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)

    showToast('下载成功')
    // 刷新下载计数
    loadShareInfo()
  } catch (err) {
    showToast('下载失败')
  } finally {
    downloading.value = false
  }
}

onMounted(loadShareInfo)
</script>

<style scoped>
.share-page {
  min-height: 100vh;
  background: linear-gradient(160deg, #e8f0fe 0%, #f5f0ff 50%, #fce4ec 100%);
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.share-card {
  background: #fff;
  border-radius: 20px;
  padding: 32px 24px;
  width: 420px;
  max-width: 95vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

/* 密码页 */
.share-icon {
  text-align: center;
  font-size: 48px;
  margin-bottom: 12px;
}
.share-title {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}
.password-input {
  margin-bottom: 16px;
}
.verify-btn {
  margin-top: 4px;
}

/* 下载页 */
.download-card {
  padding: 24px 20px;
}

/* 留言块 */
.message-block {
  background: linear-gradient(135deg, #f8f9ff, #fff5f5);
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid #eef0ff;
}
.message-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}
.message-body {
  font-size: 14px;
  color: #333;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 文件区域 */
.file-section {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}
.file-icon-large {
  font-size: 40px;
}
.file-info {
  flex: 1;
}
.file-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  word-break: break-all;
}
.file-meta {
  font-size: 12px;
  color: #999;
  display: flex;
  gap: 12px;
}

/* 文件列表 */
.file-list {
  margin-bottom: 16px;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 12px;
}
.file-item-icon {
  font-size: 28px;
}
.file-item-info {
  flex: 1;
  min-width: 0;
}
.file-item-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-item-size {
  font-size: 12px;
  color: #999;
}

/* 底部 */
.footer-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  font-size: 12px;
  color: #999;
}
.login-link {
  color: #1989fa;
  text-decoration: none;
}
</style>
