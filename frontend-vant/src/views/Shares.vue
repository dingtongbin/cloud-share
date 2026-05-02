<template>
  <div>
    <!-- 分享列表 -->
    <div
      v-for="share in shares"
      :key="share.id"
      class="share-card"
      :class="{ cancelled: !share.is_active }"
    >
      <div class="share-header" @click="toggleExpand(share)">
        <div class="share-info">
          <div class="share-file-name">{{ share.file_name }}</div>
          <div class="share-desc">{{ shareDesc(share) }}</div>
        </div>
        <van-icon
          :name="expandedId === share.id ? 'arrow-up' : 'arrow-down'"
          size="16"
          color="#999"
        />
      </div>

      <!-- 展开的操作区 -->
      <div v-if="expandedId === share.id" class="share-actions-panel">
        <!-- 留言预览 -->
        <div v-if="share.message" class="share-message-preview">
          <van-icon name="comment-o" size="14" />
          <span>{{ share.message }}</span>
        </div>

        <div class="action-row">
          <van-button size="mini" type="primary" plain @click="copyLink(share)">
            复制链接
          </van-button>
          <van-button size="mini" plain @click="showQr(share)">
            二维码
          </van-button>
          <van-button
            v-if="share.is_active"
            size="mini"
            plain
            @click="openEdit(share)"
          >
            编辑
          </van-button>
          <van-button
            v-if="share.is_active"
            size="mini"
            type="danger"
            plain
            @click="cancelShare(share)"
          >
            取消分享
          </van-button>
        </div>
      </div>
    </div>

    <van-empty v-if="!loading && shares.length === 0" description="暂无分享" />

    <!-- 二维码弹窗 -->
    <van-dialog v-model:show="showQrDialog" title="分享二维码" :show-cancel-button="false" confirmButtonText="关闭">
      <div style="text-align: center; padding: 16px;">
        <img v-if="qrUrl" :src="qrUrl" style="width: 200px;" />
        <p class="share-url-text">{{ currentShareUrl }}</p>
      </div>
    </van-dialog>

    <!-- 编辑分享弹窗 -->
    <van-popup v-model:show="showEdit" position="bottom" round :style="{ maxHeight: '80vh' }">
      <div class="popup-content">
        <div class="popup-title">编辑分享</div>
        <van-cell-group inset>
          <van-field label="有效时间">
            <template #input>
              <van-radio-group v-model="editForm.expire_hours" direction="horizontal">
                <van-radio :name="0">不修改</van-radio>
                <van-radio :name="-1">永不过期</van-radio>
                <van-radio :name="24">24小时</van-radio>
                <van-radio :name="168">7天</van-radio>
              </van-radio-group>
            </template>
          </van-field>
          <van-field
            v-model="editForm.max_downloads"
            type="number"
            label="下载次数"
            placeholder="留空不修改，0=不限"
          />
          <van-field
            v-model="editForm.password"
            label="访问密码"
            placeholder="留空不修改，清空则无密码"
          />
          <van-field
            v-model="editForm.message"
            type="textarea"
            label="分享留言"
            placeholder="给下载者的一段话（可选，最多400字）"
            :maxlength="400"
            show-word-limit
            :autosize="{ minHeight: 80 }"
          />
        </van-cell-group>
        <div style="padding: 16px;">
          <van-button round block type="primary" @click="doEdit" :loading="editing">保存修改</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import request from '../utils/request'

const shares = ref([])
const loading = ref(true)
const expandedId = ref(null)

const showQrDialog = ref(false)
const qrUrl = ref('')
const currentShareUrl = ref('')

const showEdit = ref(false)
const editShareId = ref(null)
const editing = ref(false)
const editForm = reactive({
  expire_hours: 0,
  max_downloads: '',
  password: '',
  message: '',
})

const shareDesc = (share) => {
  const parts = []
  if (share.file_size) parts.push(formatSize(share.file_size))
  parts.push(`下载 ${share.download_count}${share.max_downloads ? '/' + share.max_downloads : ''}`)
  if (!share.is_active) {
    parts.push('已取消')
  } else {
    parts.push(share.expire_at ? `过期: ${formatTime(share.expire_at)}` : '永不过期')
  }
  if (share.has_password) parts.push('🔒')
  return parts.join(' · ')
}

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

const loadShares = async () => {
  loading.value = true
  try { shares.value = await request.get('/shares/my') } finally { loading.value = false }
}

const toggleExpand = (share) => {
  expandedId.value = expandedId.value === share.id ? null : share.id
}

const copyToClipboard = (text) => {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => showToast('链接已复制'))
  } else {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    showToast('链接已复制')
  }
}

const copyLink = (share) => {
  copyToClipboard(window.location.origin + '/share/' + share.share_code)
}

const showQr = (share) => {
  currentShareUrl.value = window.location.origin + '/share/' + share.share_code
  qrUrl.value = '/api/shares/qrcode-img/' + share.share_code
  showQrDialog.value = true
}

const openEdit = (share) => {
  editShareId.value = share.id
  editForm.expire_hours = 0
  editForm.max_downloads = ''
  editForm.password = ''
  editForm.message = share.message || ''
  showEdit.value = true
}

const doEdit = async () => {
  editing.value = true
  try {
    const body = {}
    if (editForm.expire_hours !== 0) {
      body.expire_hours = editForm.expire_hours > 0 ? editForm.expire_hours : 0
    }
    if (editForm.max_downloads !== '') {
      body.max_downloads = parseInt(editForm.max_downloads) || 0
    }
    body.password = editForm.password || null
    body.message = editForm.message || null

    await request.put('/shares/' + editShareId.value, body)
    showToast('保存成功')
    showEdit.value = false
    loadShares()
  } catch {
    showToast('保存失败')
  } finally {
    editing.value = false
  }
}

const cancelShare = (share) => {
  showConfirmDialog({ title: '确认取消', message: '取消后该分享链接将失效，确定取消？' })
    .then(async () => {
      await request.patch('/shares/' + share.id + '/cancel')
      showToast('分享已取消')
      loadShares()
    }).catch(() => {})
}

onMounted(loadShares)
</script>

<style scoped>
.share-card {
  margin: 8px 12px;
  background: var(--card-bg, #fff);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.share-card.cancelled {
  opacity: 0.55;
}
.share-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
}
.share-info { flex: 1; }
.share-file-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary, #333);
  margin-bottom: 4px;
}
.share-desc {
  font-size: 12px;
  color: var(--text-secondary, #999);
}
.share-actions-panel {
  padding: 0 16px 14px;
  border-top: 1px solid var(--border-color, #f0f0f0);
}
.share-message-preview {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 0;
  font-size: 13px;
  color: var(--text-secondary, #666);
  line-height: 1.5;
}
.share-message-preview span {
  flex: 1;
}
.action-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 8px;
}
.share-url-text {
  word-break: break-all;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
.popup-content {
  max-height: 80vh;
  overflow: auto;
}
.popup-title {
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  border-bottom: 1px solid var(--border-color, #f0f0f0);
}
</style>
