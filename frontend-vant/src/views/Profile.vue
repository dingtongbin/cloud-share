<template>
  <div class="profile-page">
    <!-- 个人信息 -->
    <van-cell-group inset title="个人信息" style="margin-bottom: 12px;">
      <van-cell title="用户名" :value="user?.username" />
      <van-cell title="邮箱" :value="user?.email || '-'" />
      <van-cell title="角色" :value="user?.is_admin ? '管理员' : '普通用户'" />
      <van-cell title="存储空间">
        <template #value>
          <span>{{ storageInfo.used_formatted }} / {{ storageInfo.quota_formatted }}</span>
          <van-progress
            :percentage="storageInfo.used_percent"
            :show-pivot="false"
            :color="storageInfo.used_percent > 90 ? '#ee0a24' : storageInfo.used_percent > 70 ? '#ff976a' : '#07c160'"
            style="margin-top: 4px;"
          />
        </template>
      </van-cell>
      <van-cell title="速度限制" :value="user?.speed_limit ? user.speed_limit + ' KB/s' : '不限速'" />
      <van-cell title="注册时间" :value="user?.created_at ? formatTime(user.created_at) : '-'" />
    </van-cell-group>

    <!-- 下载记录 -->
    <van-cell-group inset title="下载记录">
      <van-cell
        v-for="log in logs"
        :key="log.id"
        :title="'文件ID: ' + log.file_id"
        :label="log.ip_address + ' · ' + formatTime(log.downloaded_at)"
      />
    </van-cell-group>
    <van-empty v-if="!loading && logs.length === 0" description="暂无下载记录" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../utils/request'

const user = ref(null)
const loading = ref(false)
const logs = ref([])
const storageInfo = ref({
  quota: 0, used_space: 0, used_percent: 0,
  quota_formatted: '0 B', used_formatted: '0 B'
})

const formatTime = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(async () => {
  loading.value = true
  try {
    const stored = localStorage.getItem('user')
    if (stored) user.value = JSON.parse(stored)
    const [logsRes, storageRes] = await Promise.all([
      request.get('/files/logs'),
      request.get('/files/storage'),
    ])
    logs.value = logsRes
    storageInfo.value = storageRes
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.profile-page { padding: 12px 0; }
</style>

