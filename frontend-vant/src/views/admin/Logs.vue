<template>
  <div>
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="loadMore">
        <van-cell-group inset>
          <van-cell
            v-for="log in logs"
            :key="log.id"
            :title="log.filename"
            :label="logDesc(log)"
          >
            <template #value>
              <van-tag size="small">{{ typeLabel(log.download_type) }}</van-tag>
            </template>
          </van-cell>
        </van-cell-group>
      </van-list>
      <van-empty v-if="!loading && logs.length === 0" description="暂无记录" />
    </van-pull-refresh>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '../../utils/request'

const logs = ref([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const page = ref(1)
const pageSize = 50
const total = ref(0)

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

const typeLabel = (type) => {
  const map = { direct: '直接下载', share: '分享下载', zip: 'ZIP下载', folder_zip: '文件夹下载' }
  return map[type] || type
}

const logDesc = (log) => {
  return `${formatSize(log.file_size)} · ${log.ip_address || '-'} · ${formatTime(log.downloaded_at)}`
}

const loadMore = async () => {
  if (loading.value) return
  loading.value = true
  try {
    const res = await request.get('/admin/download-logs', {
      params: { page: page.value, page_size: pageSize }
    })
    logs.value.push(...(res.items || []))
    total.value = res.total || 0
    page.value++
    if (logs.value.length >= total.value) finished.value = true
  } catch {
    finished.value = true
  }
  loading.value = false
}

const onRefresh = () => {
  logs.value = []
  page.value = 1
  finished.value = false
  refreshing.value = false
  loadMore()
}
</script>

