<template>
  <div class="stats-page">
    <van-grid :column-num="2" :border="false" style="margin-bottom: 12px;">
      <van-grid-item>
        <div class="stat-card">
          <van-icon name="friends-o" size="36" color="#1989fa" />
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-label">用户数</div>
          </div>
        </div>
      </van-grid-item>
      <van-grid-item>
        <div class="stat-card">
          <van-icon name="description" size="36" color="#07c160" />
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_files }}</div>
            <div class="stat-label">文件数</div>
          </div>
        </div>
      </van-grid-item>
      <van-grid-item>
        <div class="stat-card">
          <van-icon name="coupon-o" size="36" color="#ee0a24" />
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_size_str || '0 B' }}</div>
            <div class="stat-label">总存储</div>
          </div>
        </div>
      </van-grid-item>
      <van-grid-item>
        <div class="stat-card">
          <van-icon name="down" size="36" color="#ff976a" />
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_downloads }}</div>
            <div class="stat-label">下载次数</div>
          </div>
        </div>
      </van-grid-item>
    </van-grid>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../../utils/request'

const stats = ref({
  total_users: 0, total_files: 0,
  total_size: 0, total_size_str: '0 B', total_downloads: 0
})

onMounted(async () => {
  try { stats.value = await request.get('/admin/stats') } catch {}
})
</script>

<style scoped>
.stats-page { padding: 12px; }
.stat-card {
  display: flex; align-items: center; gap: 12px;
  background: var(--bg-secondary); border-radius: 12px;
  padding: 16px; width: 100%;
  box-shadow: 0 2px 8px var(--shadow-color);
}
.stat-value { font-size: 20px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-placeholder); margin-top: 2px; }
</style>

