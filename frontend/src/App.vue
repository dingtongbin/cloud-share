<template>
  <div :class="['app-container', isDark ? 'dark' : '']">
    <router-view />
  </div>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue'

const isDark = ref(false)

// 从localStorage读取主题设置
onMounted(() => {
  const saved = localStorage.getItem('theme')
  if (saved === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})

// 切换主题
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

provide('isDark', isDark)
provide('toggleTheme', toggleTheme)
</script>

<style>
.app-container {
  min-height: 100vh;
}
</style>
