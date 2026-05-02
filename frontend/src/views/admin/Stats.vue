<!--
  管理员 - 系统统计页面
-->
<template>
  <div class="stats-page">
    <el-row :gutter="20">
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-icon :size="40" color="#409eff"><UserFilled /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-label">用户数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-icon :size="40" color="#67c23a"><Document /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_files }}</div>
            <div class="stat-label">文件数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-icon :size="40" color="#e6a23c"><Coin /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_size_str || '0 B' }}</div>
            <div class="stat-label">总存储</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-icon :size="40" color="#f56c6c"><Download /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_downloads }}</div>
            <div class="stat-label">下载次数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { UserFilled, Document, Coin, Download } from "@element-plus/icons-vue";
import request from "../../utils/request";

const stats = ref({ total_users: 0, total_files: 0, total_size: 0, total_size_str: "0 B", total_downloads: 0 });

onMounted(async () => {
  try {
    stats.value = await request.get("/admin/stats");
  } catch (e) {}
});
</script>

<style scoped>
.stats-page { padding: 20px; }
.stat-card { display: flex; align-items: center; gap: 15px; padding: 20px; margin-bottom: 20px; }
.stat-value { font-size: 24px; font-weight: bold; }
.stat-label { font-size: 14px; color: var(--text-secondary); }
</style>
