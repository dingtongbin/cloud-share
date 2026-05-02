<template>
  <div :class="['layout-root', isDark ? 'dark' : '']">
    <!-- 顶部导航栏 -->
    <van-nav-bar :title="currentTitle" fixed placeholder :z-index="100">
      <template #left>
        <van-icon name="bars" size="22" @click="showSidebar = true" />
      </template>
      <template #right>
        <van-icon v-if="!isAdmin" name="info-o" size="20" style="margin-right: 12px;" @click="showStorageInfo = true" />
        <van-icon :name="isDark ? 'sun-o' : 'moon-o'" size="20" @click="toggleTheme" />
      </template>
    </van-nav-bar>

    <!-- 侧边栏抽屉 -->
    <van-popup v-model:show="showSidebar" position="left" :style="{ width: '70%', maxWidth: '300px', height: '100%' }">
      <div class="sidebar-content">
        <div class="sidebar-user" @click="goTo('/profile')">
          <div class="avatar-fallback">{{ userInitial }}</div>
          <div class="sidebar-user-info">
            <div class="sidebar-username">{{ user?.username }}</div>
            <div class="text-xs text-muted">{{ isAdmin ? '管理员' : '普通用户' }}</div>
          </div>
        </div>

        <van-cell-group inset>
          <template v-if="!isAdmin">
            <van-cell title="文件管理" icon="folder-o" is-link @click="goTo('/files')" />
            <van-cell title="我的分享" icon="share-o" is-link @click="goTo('/shares')" />
            <van-cell title="个人中心" icon="contact-o" is-link @click="goTo('/profile')" />
          </template>
          <template v-else>
            <van-cell title="用户管理" icon="friends-o" is-link @click="goTo('/admin/users')" />
            <van-cell title="下载记录" icon="orders-o" is-link @click="goTo('/admin/records')" />
            <van-cell title="操作日志" icon="todo-list-o" is-link @click="goTo('/admin/logs')" />
            <van-cell title="系统统计" icon="bar-chart-o" is-link @click="goTo('/admin/stats')" />
            <van-cell title="个人中心" icon="contact-o" is-link @click="goTo('/profile')" />
          </template>
          <van-cell title="个人设置" icon="setting-o" is-link @click="goTo('/settings')" />
        </van-cell-group>

        <div v-if="!isAdmin" class="sidebar-storage">
          <div class="text-xs text-muted mb-2">
            存储空间: {{ formatSize(usedStorage) }} / {{ formatSize(storageLimit) }}
          </div>
          <van-progress :percentage="storagePercent" :show-pivot="false" color="#1989fa" track-color="#ebedf0" />
        </div>

        <div class="sidebar-footer">
          <van-button round block plain type="danger" size="small" @click="handleLogout">退出登录</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 存储信息弹窗 -->
    <van-dialog v-model:show="showStorageInfo" title="存储空间" :show-cancel-button="false" confirmButtonText="关闭">
      <div style="padding: 16px; text-align: center;">
        <div class="mb-2">{{ formatSize(usedStorage) }} / {{ formatSize(storageLimit) }}</div>
        <van-progress :percentage="storagePercent" :show-pivot="false" stroke-width="8" color="#1989fa" />
      </div>
    </van-dialog>

    <!-- 主内容区 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import request from '../utils/request'

const router = useRouter()
const route = useRoute()

const isDark = ref(false)
const showSidebar = ref(false)
const showStorageInfo = ref(false)
const user = ref(null)
const usedStorage = ref(0)

const loadUser = () => {
  const stored = localStorage.getItem('user')
  if (stored) user.value = JSON.parse(stored)
}

const fetchStorage = async () => {
  try {
    const data = await request.get('/auth/me')
    user.value = data
    localStorage.setItem('user', JSON.stringify(data))
    usedStorage.value = data.used_space || 0
  } catch {}
}

const isAdmin = computed(() => user.value?.is_admin === true)
const storageLimit = computed(() => user.value?.quota || 0)
const storagePercent = computed(() => {
  if (storageLimit.value === 0) return 0
  return Math.min(100, Math.round((usedStorage.value / storageLimit.value) * 100))
})
const userInitial = computed(() => user.value?.username?.[0]?.toUpperCase() || '?')
const currentTitle = computed(() => route.meta?.title || 'Cloud Driver')

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0; let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

const goTo = (path) => { showSidebar.value = false; router.push(path) }

const handleLogout = () => {
  showConfirmDialog({ title: '退出确认', message: '确定要退出登录吗？' })
    .then(() => {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      showToast('已退出登录')
      router.push('/login')
    }).catch(() => {})
}

provide('isDark', isDark)
provide('toggleTheme', toggleTheme)
provide('refreshStorage', fetchStorage)
provide('currentUser', user)

onMounted(() => {
  const saved = localStorage.getItem('theme')
  if (saved === 'dark') { isDark.value = true; document.documentElement.classList.add('dark') }
  loadUser()
  fetchStorage()
})

watch(() => route.path, () => { fetchStorage() })
</script>

<style scoped>
.layout-root { min-height: 100vh; background: var(--bg-primary); }
.main-content { padding: 12px; min-height: calc(100vh - 46px); }
.sidebar-content { height: 100%; display: flex; flex-direction: column; background: var(--bg-secondary); }
.sidebar-user { padding: 24px 16px 16px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--border-color); cursor: pointer; }
.sidebar-user:active { background: var(--bg-tertiary); }
.avatar-fallback { width: 48px; height: 48px; background: #1989fa; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 20px; font-weight: bold; }
.sidebar-username { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.sidebar-storage { padding: 16px; border-top: 1px solid var(--border-color); }
.sidebar-footer { padding: 16px; margin-top: auto; border-top: 1px solid var(--border-color); }
</style>
