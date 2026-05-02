<template>
  <div>
    <el-card v-for="share in shares" :key="share.id" class="mb-4">
      <div class="flex items-center justify-between" style="flex-wrap: wrap; gap: 12px;">
        <div>
          <div class="flex items-center gap-2">
            <span style="font-size: 20px;">📄</span>
            <strong>{{ share.file_name }}</strong>
          </div>
          <div class="text-sm text-muted mt-2">
            <span v-if="share.file_size" class="mr-4">{{ formatSize(share.file_size) }}</span>
            <span class="mr-4">下载 {{ share.download_count }}{{ share.max_downloads ? `/${share.max_downloads}` : '' }}</span>
            <span v-if="share.expire_at">过期: {{ formatTime(share.expire_at) }}</span>
            <span v-else>永不过期</span>
            <span v-if="share.has_password" class="ml-4">🔒 密码保护</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <el-button size="small" @click="copyLink(share.share_code)">复制链接</el-button>
          <el-button size="small" @click="showQr(share.share_code)">二维码</el-button>
          <el-button size="small" type="danger" @click="deleteShare(share.id)">删除</el-button>
        </div>
      </div>
    </el-card>

    <el-empty v-if="!loading && shares.length === 0" description="暂无分享" />

    <!-- 二维码对话框 -->
    <el-dialog v-model="showQrDialog" title="分享二维码" width="350px">
      <div style="text-align: center;">
        <img v-if="qrUrl" :src="qrUrl" style="width: 200px;" />
        <p class="text-muted mt-2">{{ currentShareUrl }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const shares = ref([])
const loading = ref(true)
const showQrDialog = ref(false)
const qrUrl = ref('')
const currentShareUrl = ref('')

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
  try {
    shares.value = await request.get('/shares/my')
  } finally {
    loading.value = false
  }
}

const copyLink = (shareCode) => {
  const url = `${window.location.origin}/share/${shareCode}`
  navigator.clipboard.writeText(url)
  ElMessage.success('链接已复制')
}

const showQr = (shareCode) => {
  currentShareUrl.value = `${window.location.origin}/share/${shareCode}`
  qrUrl.value = `/api/shares/qrcode-img/${shareCode}`
  showQrDialog.value = true
}

const deleteShare = async (shareId) => {
  await ElMessageBox.confirm('确定删除此分享链接？', '确认', { type: 'warning' })
  await request.delete(`/shares/${shareId}`)
  ElMessage.success('已删除')
  loadShares()
}

onMounted(loadShares)
</script>
