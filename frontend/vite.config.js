import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    allowedHosts: ['blog.dingtongbin.cn'],
    port: 29001,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:29000',
        changeOrigin: true,
      },
      '/share': {
        target: 'http://localhost:29000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'vant': ['vant'],
          'vendor': ['vue', 'vue-router', 'pinia', 'axios'],
        },
      },
    },
  },
})
