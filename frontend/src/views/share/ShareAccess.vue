<!--
  分享访问页面 - 公开页面,用于下载分享的文件
  支持密码验证
-->
<template>
  <div class="share-access">
    <div class="share-box">
      <div class="share-header">
        <el-icon :size="50" color="#409eff"><FolderOpened /></el-icon>
        <h1>Cloud Driver</h1>
        <p>文件分享</p>
      </div>

      <div v-if="loading" class="share-loading">
        <el-icon class="is-loading" :size="30"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <div v-else-if="error" class="share-error">
        <el-icon :size="40" color="#f56c6c"><CircleClose /></el-icon>
        <p>{{ error }}</p>
        <el-button type="primary" @click="$router.push('/login')">前往登录</el-button>
      </div>

      <div v-else class="share-info">
        <el-card>
          <div class="file-info">
            <el-icon :size="30" color="#409eff"><Document /></el-icon>
            <div>
              <h3>{{ shareData.file_name }}</h3>
              <p class="file-meta">
                大小: {{ formatSize(shareData.file_size) }}
                <span v-if="shareData.max_downloads"> | 剩余下载: {{ shareData.max_downloads - shareData.download_count }}</span>
                <span v-if="shareData.expire_at"> | 过期: {{ new Date(shareData.expire_at).toLocaleString('zh-CN') }}</span>
              </p>
            </div>
          </div>
        </el-card>

        <div v-if="needPassword" class="password-section">
          <el-input v-model="password" placeholder="请输入提取密码" type="password" show-password />
          <el-button type="primary" @click="verifyPassword">验证</el-button>
        </div>

        <el-button
          v-if="!needPassword || verified"
          type="primary"
          size="large"
          class="download-btn"
          @click="download"
        >
          <el-icon><Download /></el-icon>
          下载文件
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { FolderOpened, Document, Loading, CircleClose, Download } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "../../utils/request";

const route = useRoute();
const loading = ref(true);
const error = ref("");
const shareData = ref({});
const needPassword = ref(false);
const verified = ref(false);
const password = ref("");

const formatSize = (bytes) => {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0, size = bytes;
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
  return `${size.toFixed(2)} ${units[i]}`;
};

const loadShareInfo = async () => {
  loading.value = true;
  try {
    const res = await request.get(`/shares/access/${route.params.code}`);
    shareData.value = res;
    needPassword.value = res.need_password;
    if (!needPassword.value) verified.value = true;
  } catch (e) {
    error.value = "分享链接不存在或已失效";
  }
  loading.value = false;
};

const verifyPassword = async () => {
  try {
    await request.post(`/shares/verify/${route.params.code}`, { password: password.value });
    verified.value = true;
    needPassword.value = false;
    ElMessage.success("验证成功");
  } catch (e) {
    ElMessage.error("密码错误");
  }
};

const download = () => {
  const url = password.value
    ? `/api/shares/download/${route.params.code}?password=${encodeURIComponent(password.value)}`
    : `/api/shares/download/${route.params.code}`;
  window.open(url, "_blank");
};

onMounted(loadShareInfo);
</script>

<style scoped>
.share-access {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.share-box {
  width: 450px;
  max-width: 90vw;
  background: #fff;
  border-radius: 12px;
  padding: 40px 30px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  text-align: center;
}

.share-header h1 { margin: 10px 0 5px; font-size: 24px; color: #303133; }
.share-header p { color: #909399; }

.share-loading, .share-error {
  padding: 30px 0;
}

.share-error p {
  margin: 15px 0;
  color: #f56c6c;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 15px;
  text-align: left;
}

.file-info h3 { margin: 0 0 5px; }
.file-meta { color: #909399; font-size: 13px; }

.password-section {
  margin: 20px 0;
  display: flex;
  gap: 10px;
}

.download-btn {
  width: 100%;
  margin-top: 20px;
  height: 50px;
  font-size: 16px;
}
</style>
