<!--
  个人中心 - 用户信息和下载记录
-->
<template>
  <div class="profile-page">
    <el-card shadow="never" style="margin-bottom:16px">
      <template #header><span style="font-weight:600">个人信息</span></template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ userStore.user.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ userStore.user.email }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ userStore.isAdmin ? "管理员" : "普通用户" }}</el-descriptions-item>
        <el-descriptions-item label="存储空间">
          <div>
            <span>{{ storageInfo.used_formatted }} / {{ storageInfo.quota_formatted }}</span>
            <el-progress :percentage="storageInfo.used_percent" :stroke-width="8" style="margin-top:5px"
              :color="storageInfo.used_percent > 90 ? '#F56C6C' : storageInfo.used_percent > 70 ? '#E6A23C' : '#67C23A'" />
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="速度限制">
          {{ userStore.user.speed_limit ? userStore.user.speed_limit + " KB/s" : "不限速" }}
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">
          {{ userStore.user.created_at ? new Date(userStore.user.created_at).toLocaleString("zh-CN") : "-" }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never">
      <template #header><span style="font-weight:600">下载记录</span></template>
      <el-table :data="logs" stripe v-loading="loading" max-height="400" empty-text="暂无记录">
        <el-table-column label="文件ID" prop="file_id" width="100" />
        <el-table-column label="IP地址" prop="ip_address" width="150" />
        <el-table-column label="下载时间">
          <template #default="{ row }">
            {{ row.downloaded_at ? new Date(row.downloaded_at).toLocaleString("zh-CN") : "-" }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useUserStore } from "../stores/user";
import request from "../utils/request";

const userStore = useUserStore();
const loading = ref(false);
const logs = ref([]);
const storageInfo = ref({ quota: 0, used_space: 0, used_percent: 0, quota_formatted: "0 B", used_formatted: "0 B" });

onMounted(async () => {
  loading.value = true;
  try {
    const [logsRes, storageRes] = await Promise.all([
      request.get("/api/files/logs"),
      request.get("/api/files/storage"),
    ]);
    logs.value = logsRes;
    storageInfo.value = storageRes;
  } catch {}
  loading.value = false;
});
</script>

<style scoped>
.profile-page { padding: 16px; max-width: 800px; }
</style>
