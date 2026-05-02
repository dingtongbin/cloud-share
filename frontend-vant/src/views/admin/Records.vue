<template>
  <div>
    <van-cell-group inset title="下载记录">
      <van-cell v-for="rec in records" :key="rec.id" :title="rec.filename" :label="recDesc(rec)">
        <template #value>
          <van-tag size="small">{{ typeLabel(rec.download_type) }}</van-tag>
        </template>
      </van-cell>
    </van-cell-group>

    <van-empty v-if="!loading && records.length === 0" description="暂无记录" />

    <!-- 分页 -->
    <div v-if="total > pageSize" class="flex justify-between items-center mt-4" style="padding: 0 16px;">
      <span class="text-xs text-muted">共 {{ total }} 条</span>
      <div class="flex gap-2">
        <van-button size="mini" :disabled="page <= 1" @click="page--; loadRecords()">上一页</van-button>
        <span class="text-sm">{{ page }}/{{ totalPages }}</span>
        <van-button size="mini" :disabled="page >= totalPages" @click="page++; loadRecords()">下一页</van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '../../utils/request'

const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const loading = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const recDesc = (rec) => {
  const size = (bytes) => {
    if (!bytes) return '-'
    const units = ['B', 'KB', 'MB', 'GB']
    let i = 0, s = bytes
    while (s >= 1024 && i < 3) { s /= 1024; i++ }
    return `${s.toFixed(1)} ${units[i]}`
  }
  const time = rec.downloaded_at ? new Date(rec.downloaded_at).toLocaleString('zh-CN') : '-'
  return `${size(rec.file_size)} · ${rec.ip_address || '-'} · ${time}`
}

const typeLabel = (type) => {
  const map = { direct: '直接下载', share: '分享下载', zip: 'ZIP下载', folder_zip: '文件夹下载' }
  return map[type] || type
}

const loadRecords = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/download-logs', { params: { page: page.value, page_size: pageSize } })
    records.value = res.items || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(loadRecords)
</script>
