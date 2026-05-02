<template>
  <div :class="['layout-root', isDark ? 'dark' : '']">
    <!-- 移动端遮罩 -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false"></div>

    <!-- 侧边栏 -->
    <aside :class="['sidebar', sidebarOpen ? 'open' : '']">
      <div class="sidebar-logo">
        <img src="/logo.svg" alt="Logo" class="sidebar-logo-img" />
        <span>Cloud Driver</span>
      </div>

      <el-menu
        class="sidebar-menu"
        :default-active="activeMenu"
        router
        @select="sidebarOpen = false"
      >
        <!-- 普通用户菜单 -->
        <template v-if="!isAdmin">
          <el-menu-item index="/files">
            <el-icon><Folder /></el-icon>
            <span>文件管理</span>
          </el-menu-item>
          <el-menu-item index="/shares">
            <el-icon><Share /></el-icon>
            <span>我的分享</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>个人设置</span>
          </el-menu-item>
        </template>

        <!-- 管理员菜单 -->
        <template v-else>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/records">
            <el-icon><Document /></el-icon>
            <span>下载记录</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>个人设置</span>
          </el-menu-item>
        </template>
      </el-menu>

      <div class="sidebar-footer">
        <div class="flex items-center gap-2">
          <el-avatar :size="32" :style="{ background: isAdmin ? '#f56c6c' : '#409eff' }">
            {{ user?.username?.[0]?.toUpperCase() }}
          </el-avatar>
          <div>
            <div class="text-sm">{{ user?.username }}</div>
            <div class="text-xs text-muted">{{ isAdmin ? u7ba1u7406u5458 : u666eu901au7528u6237 }}</div>
          </div>
        </div>
        <el-button text type="danger" size="small" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="main-header">
        <div class="flex items-center gap-2">
          <span class="mobile-menu-btn" @click="sidebarOpen = !sidebarOpen">☰</span>
          <h3>{{ currentTitle }}</h3>
        </div>
        <div class="flex items-center gap-2">
          <!-- 存储空间(仅普通用户) -->
          <template v-if="!isAdmin">
            <el-tooltip :content="storageTooltip">
              <el-progress
                :percentage="storagePercent"
                :stroke-width="6"
                :show-text="false"
                style="width: 100px;"
              />
            </el-tooltip>
          </template>
          <!-- 主题切换 -->
          <el-button circle @click="toggleTheme">
            <el-icon><Sunny v-if="isDark" /><Moon v-else /></el-icon>
          </el-button>
        </div>
      </header>

      <div class="main-page">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const route = useRoute()

const isDark = ref(false)
const sidebarOpen = ref(false)
const user = ref(null)
const usedStorage = ref(0)

// 读取用户信息
const loadUser = () => {
  const stored = localStorage.getItem('user')
  if (stored) user.value = JSON.parse(stored)
}

// 获取最新存储使用量
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
const storageTooltip = computed(() => {
  return `已用 ${formatSize(usedStorage.value)} / ${formatSize(storageLimit.value)}`
})

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || 'Cloud Driver')

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const units = [ 'B', 'KB', 'MB', 'GB', 'TB' ]
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
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

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '退出确认',
      {
        confirmButtonText: '确定退出',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}

provide('isDark', isDark)
provide('toggleTheme', toggleTheme)
provide('refreshStorage', fetchStorage)
provide('currentUser', user)

onMounted(() => {
  // 主题初始化
  const saved = localStorage.getItem('theme')
  if (saved === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
  loadUser()
  fetchStorage()
})

watch(() => route.path, () => {
  fetchStorage()
})
</script>

<style scoped>
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 99;
  display: none;
}

.sidebar-logo-img {
  width: 28px;
  height: 28px;
}

@media (max-width: 768px) {
  .sidebar-overlay {
    display: block;
  }
}
</style>
