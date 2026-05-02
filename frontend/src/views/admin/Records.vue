<template>
  <div>
    <el-card>
      <template #header>下载记录</template>
      <el-table :data="records" style="width: 100%" v-loading="loading">
        <el-table-column prop="user_id" label="用户ID" width="80" />
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column label="大小" width="120">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ typeLabel(row.download_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column label="下载时间" width="180">
          <template #default="{ row }">{{ formatTime(row.downloaded_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="mt-4 flex justify-between items-center">
        <span class="text-muted">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadRecords"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../../utils/request'

const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const loading = ref(false)

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

const loadRecords = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/download-logs', {
      params: { page: page.value, page_size: pageSize },
    })
    records.value = res.items || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(loadRecords)
</script>
