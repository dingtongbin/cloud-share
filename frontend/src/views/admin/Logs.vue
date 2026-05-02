<!--
  管理员 - 下载记录页面
-->
<template>
  <div class="logs-page">
    <div class="toolbar">
      <el-button :icon="Refresh" @click="loadLogs">刷新</el-button>
    </div>
    <el-table :data="logs" stripe v-loading="loading" max-height="600">
      <el-table-column label="ID" prop="id" width="60" />
      <el-table-column label="用户" prop="username" width="120" />
      <el-table-column label="文件名" prop="filename" min-width="200" />
      <el-table-column label="IP地址" prop="ip_address" width="150" />
      <el-table-column label="下载时间" width="200">
        <template #default="{ row }">
          {{ row.downloaded_at ? new Date(row.downloaded_at).toLocaleString("zh-CN") : "-" }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "../../utils/request";

const loading = ref(false);
const logs = ref([]);

const loadLogs = async () => {
  loading.value = true;
  try {
    const res = await request.get("/admin/download-logs");
    logs.value = res.items || [];
  } catch (e) {
    ElMessage.error("加载失败");
  }
  loading.value = false;
};

onMounted(loadLogs);
</script>

<style scoped>
.logs-page { padding: 20px; }
.toolbar { margin-bottom: 15px; }
</style>
