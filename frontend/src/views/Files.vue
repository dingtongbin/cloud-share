<template>
  <div class="files-page">
    <!-- 操作工具栏 -->
    <div class="toolbar flex items-center justify-between mb-4" style="flex-wrap: wrap; gap: 8px;">
      <div class="flex items-center gap-2">
        <el-button type="primary" @click="triggerUpload">
          <el-icon><Upload /></el-icon> 上传文件
        </el-button>
        <el-button @click="triggerUploadFolder">
          <el-icon><FolderAdd /></el-icon> 上传文件夹
        </el-button>
        <el-button @click="showCreateFolder = true">
          <el-icon><FolderAdd /></el-icon> 新建文件夹
        </el-button>
        <input ref="fileInput" type="file" multiple hidden @change="handleUploadFiles" />
        <input ref="folderInput" type="file" webkitdirectory multiple hidden @change="handleUploadFolder" />
      </div>
      <div class="flex items-center gap-2">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button value="grid">
            <el-icon><Grid /></el-icon>
          </el-radio-button>
          <el-radio-button value="list">
            <el-icon><List /></el-icon>
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 面包屑路径 -->
    <div class="path-bar">
      <span class="path-item" @click="navigateTo('/')">📁 根目录</span>
      <template v-for="(seg, i) in pathSegments" :key="i">
        <span class="path-separator">/</span>
        <span
          :class="i === pathSegments.length - 1 ? 'path-current' : 'path-item'"
          @click="i < pathSegments.length - 1 && navigateTo(buildPath(i))"
        >{{ seg }}</span>
      </template>
    </div>

    <!-- 上传进度 -->
    <el-progress v-if="uploading" :percentage="uploadPercent" :status="uploadPercent === 100 ? 'success' : ''" class="mb-4" />

    <!-- 文件网格视图 -->
    <template v-if="viewMode === 'grid'">
      <div class="file-grid">
        <!-- 文件夹 -->
        <div
          v-for="folder in folders"
          :key="'f-' + folder.id"
          class="file-card"
          @dblclick="navigateTo(folder.file_path)"
          @contextmenu.prevent="onFolderContext($event, folder)"
        >
          <div class="file-icon">📁</div>
          <div class="file-name">{{ folder.original_name }}</div>
          <div class="file-size">文件夹</div>
        </div>
        <!-- 文件 -->
        <div
          v-for="file in files"
          :key="file.id"
          class="file-card"
          @click="previewFile(file)"
          @contextmenu.prevent="onFileContext($event, file)"
        >
          <div class="file-icon">{{ getFileIcon(file.original_name) }}</div>
          <div class="file-name">{{ file.original_name }}</div>
          <div class="file-size">{{ formatSize(file.file_size) }}</div>
        </div>
      </div>
    </template>

    <!-- 文件列表视图 -->
    <template v-else>
      <el-table :data="[...folders.map(f => ({...f, _type: 'folder'})), ...files.map(f => ({...f, _type: 'file'}))]"
        style="width: 100%" @row-click="onRowClick" @row-contextmenu="onRowContext">
        <el-table-column label="名称" min-width="250">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <span>{{ row._type === 'folder' ? '📁' : getFileIcon(row.original_name) }}</span>
              <span>{{ row._type === 'folder' ? row.original_name : row.original_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="120">
          <template #default="{ row }">
            {{ row._type === 'folder' ? '文件夹' : formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="修改时间" width="180">
          <template #default="{ row }">
            {{ row._type === 'file' ? formatTime(row.updated_at || row.created_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row._type === 'file'">
              <el-button text size="small" @click.stop="downloadFile(row)">下载</el-button>
              <el-button text size="small" @click.stop="createShare(row)">分享</el-button>
              <el-dropdown trigger="click" @command="cmd => handleFileCommand(cmd, row)">
                <el-button text size="small">更多</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rename">重命名</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
            <template v-else>
              <el-button text size="small" @click.stop="downloadFolder(row)">下载ZIP</el-button>
              <el-button text size="small" type="danger" @click.stop="deleteFolderConfirm(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <!-- 空状态 -->
    <el-empty v-if="!loading && folders.length === 0 && files.length === 0" description="此文件夹为空" />

    <!-- 右键菜单 -->
    <div v-if="contextMenu.visible" class="context-menu" :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }">
      <template v-if="contextMenu.type === 'file'">
        <div class="context-item" @click="previewFile(contextMenu.data)">预览</div>
        <div class="context-item" @click="downloadFile(contextMenu.data)">下载</div>
        <div class="context-item" @click="createShare(contextMenu.data)">分享</div>
        <div class="context-item" @click="renameFile(contextMenu.data)">重命名</div>
        <div class="context-item danger" @click="deleteFileConfirm(contextMenu.data)">删除</div>
      </template>
      <template v-else>
        <div class="context-item" @click="navigateTo(contextMenu.data.file_path)">打开</div>
        <div class="context-item" @click="downloadFolder(contextMenu.data)">下载ZIP</div>
        <div class="context-item danger" @click="deleteFolderConfirm(contextMenu.data)">删除</div>
      </template>
    </div>

    <!-- 创建文件夹对话框 -->
    <el-dialog v-model="showCreateFolder" title="新建文件夹" width="400px">
      <el-input v-model="newFolderName" placeholder="请输入文件夹名称" @keyup.enter="createFolder" />
      <template #footer>
        <el-button @click="showCreateFolder = false">取消</el-button>
        <el-button type="primary" @click="createFolder">创建</el-button>
      </template>
    </el-dialog>

    <!-- 重命名对话框 -->
    <el-dialog v-model="showRename" title="重命名" width="400px">
      <el-input v-model="newFileName" placeholder="请输入新文件名" @keyup.enter="doRename" />
      <template #footer>
        <el-button @click="showRename = false">取消</el-button>
        <el-button type="primary" @click="doRename">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分享对话框 -->
    <el-dialog v-model="showShare" title="创建分享链接" width="500px">
      <el-form :model="shareForm" label-width="100px">
        <el-form-item label="有效时间">
          <el-select v-model="shareForm.expire_hours" placeholder="永不过期" clearable>
            <el-option :value="1" label="1小时" />
            <el-option :value="6" label="6小时" />
            <el-option :value="24" label="24小时" />
            <el-option :value="72" label="3天" />
            <el-option :value="168" label="7天" />
          </el-select>
        </el-form-item>
        <el-form-item label="下载次数">
          <el-input-number v-model="shareForm.max_downloads" :min="0" :step="1" placeholder="不限制" />
          <span class="text-muted" style="margin-left: 8px;">0=不限制</span>
        </el-form-item>
        <el-form-item label="访问密码">
          <el-input v-model="shareForm.password" placeholder="留空则无密码" />
        </el-form-item>
      </el-form>

      <div v-if="shareResult" class="share-result mt-4" style="text-align: center;">
        <p class="mb-2">分享链接已创建：</p>
        <el-input :value="shareUrl" readonly>
          <template #append>
            <el-button @click="copyShareUrl">复制</el-button>
          </template>
        </el-input>
        <img v-if="shareQrUrl" :src="shareQrUrl" style="width: 180px; margin-top: 12px;" />
      </div>

      <template #footer>
        <el-button @click="showShare = false">关闭</el-button>
        <el-button v-if="!shareResult" type="primary" @click="doCreateShare">创建</el-button>
      </template>
    </el-dialog>

    <!-- 文件预览对话框 -->
    <el-dialog v-model="showPreview" :title="previewFileData?.original_name || '文件预览'" width="80%" top="5vh" destroy-on-close>
      <div v-if="previewData" class="preview-content">
        <!-- 文本预览 -->
        <template v-if="previewData.type === 'text'">
          <div class="flex items-center justify-between mb-2">
            <span></span>
            <el-button v-if="!editing" size="small" @click="startEdit">编辑</el-button>
            <div v-else class="flex gap-2">
              <el-button size="small" type="primary" @click="saveEdit">保存</el-button>
              <el-button size="small" @click="cancelEdit">取消</el-button>
            </div>
          </div>
          <el-input
            v-if="editing"
            v-model="editContent"
            type="textarea"
            :rows="20"
            style="font-family: monospace;"
          />
          <pre v-else style="background: var(--bg-tertiary); padding: 16px; border-radius: 8px; overflow: auto; max-height: 60vh; font-family: monospace; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-all;">{{ previewData.content }}</pre>
        </template>
        <!-- 图片预览 -->
        <template v-else-if="previewData.type === 'image'">
          <img :src="previewData.url" style="max-width: 100%; border-radius: 8px;" />
        </template>
        <!-- 视频预览 -->
        <template v-else-if="previewData.type === 'media'">
          <video v-if="previewData.content_type?.startsWith('video')" :src="previewData.url" controls style="max-width: 100%;" />
          <audio v-else :src="previewData.url" controls style="width: 100%;" />
        </template>
        <!-- PDF预览 -->
        <template v-else-if="previewData.type === 'pdf'">
          <iframe :src="previewData.url" style="width: 100%; height: 70vh; border: none;" />
        </template>
        <!-- 不支持预览 -->
        <template v-else>
          <div class="text-center">
            <p>该文件类型不支持在线预览</p>
            <el-button type="primary" class="mt-4" @click="downloadFile(previewFileData)">下载文件</el-button>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, inject, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const currentPath = ref('/')
const folders = ref([])
const files = ref([])
const loading = ref(false)
const viewMode = ref('grid')
const refreshStorage = inject('refreshStorage')

// 上传
const fileInput = ref()
const folderInput = ref()
const uploading = ref(false)
const uploadPercent = ref(0)

// 创建文件夹
const showCreateFolder = ref(false)
const newFolderName = ref('')

// 重命名
const showRename = ref(false)
const newFileName = ref('')
const renameFileId = ref(null)

// 分享
const showShare = ref(false)
const shareForm = reactive({
  expire_hours: null,
  max_downloads: 0,
  password: '',
  file_id: null,
})
const shareResult = ref(false)
const shareUrl = ref('')
const shareQrUrl = ref('')

// 预览
const showPreview = ref(false)
const previewData = ref(null)
const previewFileData = ref(null)
const editing = ref(false)
const editContent = ref('')
const editingFileId = ref(null)

// 右键菜单
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  type: 'file',
  data: null,
})

// 路径计算
const pathSegments = computed(() => {
  if (currentPath.value === '/') return []
  return currentPath.value.split('/').filter(Boolean)
})

const buildPath = (index) => {
  return '/' + pathSegments.value.slice(0, index + 1).join('/')
}

const navigateTo = (path) => {
  currentPath.value = path || '/'
  loadFiles()
}

// 格式化文件大小
const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

// 格式化时间
const formatTime = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

// 获取文件图标
const getFileIcon = (name) => {
  if (!name) return '📄'
  const ext = name.split('.').pop().toLowerCase()
  const icons = {
    jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', webp: '🖼️', svg: '🖼️', bmp: '🖼️',
    mp4: '🎬', avi: '🎬', mkv: '🎬', mov: '🎬', webm: '🎬',
    mp3: '🎵', wav: '🎵', flac: '🎵', ogg: '🎵',
    pdf: '📕', doc: '📝', docx: '📝', txt: '📝', md: '📝',
    xls: '📊', xlsx: '📊', csv: '📊',
    ppt: '📽️', pptx: '📽️',
    zip: '📦', rar: '📦', '7z': '📦', tar: '📦', gz: '📦',
    js: '💻', ts: '💻', py: '💻', java: '💻', c: '💻', cpp: '💻', html: '💻', css: '💻', json: '💻',
    exe: '⚙️', sh: '⚙️', bat: '⚙️',
  }
  return icons[ext] || '📄'
}

// 加载文件列表
const loadFiles = async () => {
  loading.value = true
  try {
    const res = await request.get('/files/list', { params: { folder: currentPath.value } })
    folders.value = res.folders || []
    files.value = res.files || []
  } finally {
    loading.value = false
  }
}

// 上传文件
const triggerUpload = () => fileInput.value?.click()

const handleUploadFiles = async (e) => {
  const fileList = e.target.files
  if (!fileList.length) return
  
  uploading.value = true
  uploadPercent.value = 0
  
  for (let i = 0; i < fileList.length; i++) {
    const fd = new FormData()
    fd.append('file', fileList[i])
    try {
      await request.post('/files/upload', fd, {
        params: { folder: currentPath.value },
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (evt) => {
          uploadPercent.value = Math.round(((i + evt.loaded / (evt.total || 1)) / fileList.length) * 100)
        },
      })
    } catch (err) {
      ElMessage.error(`上传失败: ${fileList[i].name}`)
    }
  }
  
  uploadPercent.value = 100
  uploading.value = false
  fileInput.value.value = ''
  ElMessage.success('上传完成')
  loadFiles()
  refreshStorage?.()
}

// 上传文件夹
const triggerUploadFolder = () => folderInput.value?.click()

const handleUploadFolder = async (e) => {
  const fileList = e.target.files
  if (!fileList.length) return
  
  uploading.value = true
  uploadPercent.value = 0
  const fd = new FormData()
  
  for (let i = 0; i < fileList.length; i++) {
    const f = fileList[i]
    // 保留webkitRelativePath作为文件名以保持目录结构
    const blob = new Blob([await f.arrayBuffer()], { type: f.type })
    const newFile = new File([blob], f.webkitRelativePath || f.name, { type: f.type })
    fd.append('files', newFile)
  }
  
  try {
    await request.post('/files/upload/folder', fd, {
      params: { folder: currentPath.value },
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (evt.total) uploadPercent.value = Math.round((evt.loaded / evt.total) * 100)
      },
    })
    ElMessage.success('文件夹上传完成')
  } catch (err) {
    ElMessage.error('文件夹上传失败')
  }
  
  uploadPercent.value = 100
  uploading.value = false
  folderInput.value.value = ''
  loadFiles()
  refreshStorage?.()
}

// 创建文件夹
const createFolder = async () => {
  if (!newFolderName.value.trim()) {
    ElMessage.warning('请输入文件夹名称')
    return
  }
  await request.post('/files/folder', { name: newFolderName.value, parent: currentPath.value })
  ElMessage.success('文件夹创建成功')
  showCreateFolder.value = false
  newFolderName.value = ''
  loadFiles()
}

// 下载文件
const downloadFile = (file) => {
  const token = localStorage.getItem('token')
  fetch(`/api/files/download/${file.id}`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then(res => res.blob()).then(blob => {
    const u = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = u
    link.download = file.original_name
    link.click()
    URL.revokeObjectURL(u)
  })
}

// 下载文件夹
const downloadFolder = (folder) => {
  const token = localStorage.getItem('token')
  fetch(`/api/files/download-folder?folder=${encodeURIComponent(folder.file_path)}`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then(res => res.blob()).then(blob => {
    const u = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = u
    link.download = `${folder.original_name}.zip`
    link.click()
    URL.revokeObjectURL(u)
  })
}

// 预览文件
const fetchBlobUrl = async (fileId) => {
  const token = localStorage.getItem('token')
  const res = await fetch(`/api/files/preview/${fileId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('预览请求失败')
  const blob = await res.blob()
  return URL.createObjectURL(blob)
}

const revokePreviewUrl = () => {
  if (previewData.value?.url?.startsWith('blob:')) {
    URL.revokeObjectURL(previewData.value.url)
  }
}

const previewFile = async (file) => {
  previewFileData.value = file
  revokePreviewUrl()
  try {
    const mime = file.mime_type || ''
    if (mime.startsWith('text/') || mime === 'application/json' || mime === 'application/javascript') {
      const res = await request.get(`/files/content/${file.id}`)
      previewData.value = { type: 'text', content: res.content }
    } else if (mime.startsWith('image/')) {
      const url = await fetchBlobUrl(file.id)
      previewData.value = { type: 'image', url }
    } else if (mime.startsWith('video/') || mime.startsWith('audio/')) {
      const url = await fetchBlobUrl(file.id)
      previewData.value = { type: 'media', content_type: mime, url }
    } else if (mime === 'application/pdf') {
      const url = await fetchBlobUrl(file.id)
      previewData.value = { type: 'pdf', url }
    } else {
      previewData.value = { type: 'unknown' }
    }
    editing.value = false
    showPreview.value = true
  } catch {
    ElMessage.error('预览失败')
  }
}

// 在线编辑
const startEdit = async () => {
  try {
    const res = await request.get(`/files/content/${previewFileData.value.id}`)
    editContent.value = res.content
    editingFileId.value = previewFileData.value.id
    editing.value = true
  } catch {
    ElMessage.error('获取文件内容失败')
  }
}

const saveEdit = async () => {
  try {
    await request.put(`/files/content/${editingFileId.value}`, { content: editContent.value })
    ElMessage.success('保存成功')
    editing.value = false
    previewData.value.content = editContent.value
  } catch {
    ElMessage.error('保存失败')
  }
}

const cancelEdit = () => {
  editing.value = false
}

// 重命名
const renameFile = (file) => {
  renameFileId.value = file.id
  newFileName.value = file.original_name
  showRename.value = true
  contextMenu.visible = false
}

const doRename = async () => {
  if (!newFileName.value.trim()) {
    ElMessage.warning('请输入新文件名')
    return
  }
  await request.put(`/files/rename/${renameFileId.value}`, { new_name: newFileName.value })
  ElMessage.success('重命名成功')
  showRename.value = false
  loadFiles()
}

// 删除文件
const deleteFileConfirm = async (file) => {
  contextMenu.visible = false
  await ElMessageBox.confirm(`确定删除文件 "${file.original_name}"？`, '确认删除', { type: 'warning' })
  await request.delete(`/files/${file.id}`)
  ElMessage.success('文件已删除')
  loadFiles()
  refreshStorage?.()
}

// 删除文件夹
const deleteFolderConfirm = async (folder) => {
  contextMenu.visible = false
  await ElMessageBox.confirm(`确定删除文件夹 "${folder.original_name}" 及其所有内容？`, '确认删除', { type: 'warning' })
  const path = folder.file_path.startsWith('/') ? folder.file_path.slice(1) : folder.file_path
  await request.delete(`/files/folder/${path}`)
  ElMessage.success('文件夹已删除')
  loadFiles()
  refreshStorage?.()
}

// 创建分享
const createShare = (file) => {
  shareForm.file_id = file.id
  shareForm.expire_hours = null
  shareForm.max_downloads = 0
  shareForm.password = ''
  shareResult.value = false
  showShare.value = true
  contextMenu.visible = false
}

const doCreateShare = async () => {
  try {
    const res = await request.post('/shares', {
      file_id: shareForm.file_id,
      expire_hours: shareForm.expire_hours || 0,
      max_downloads: shareForm.max_downloads || 0,
      password: shareForm.password || null,
    })
    const baseUrl = window.location.origin
    shareUrl.value = `${baseUrl}/share/${res.share_code}`
    shareQrUrl.value = `/api/shares/qrcode-img/${res.share_code}`
    shareResult.value = true
    ElMessage.success('分享链接创建成功')
  } catch (err) {
    // error handled by interceptor
  }
}

const copyShareUrl = () => {
  navigator.clipboard.writeText(shareUrl.value)
  ElMessage.success('已复制到剪贴板')
}

// 右键菜单处理
const onFileContext = (e, file) => {
  e.preventDefault()
  contextMenu.visible = true
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.type = 'file'
  contextMenu.data = file
}

const onFolderContext = (e, folder) => {
  e.preventDefault()
  contextMenu.visible = true
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.type = 'folder'
  contextMenu.data = folder
}

const onRowContext = (row, column, event) => {
  if (row._type === 'file') {
    onFileContext(event, row)
  } else {
    onFolderContext(event, row)
  }
}

const onRowClick = (row) => {
  if (row._type === 'folder') {
    navigateTo(row.file_path)
  } else {
    previewFile(row)
  }
}

const handleFileCommand = (cmd, file) => {
  if (cmd === 'rename') renameFile(file)
  if (cmd === 'delete') deleteFileConfirm(file)
}

// 点击空白关闭右键菜单
const closeContextMenu = () => {
  contextMenu.visible = false
}

watch(showPreview, (val) => {
  if (!val) revokePreviewUrl()
})

onMounted(() => {
  loadFiles()
  document.addEventListener('click', closeContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
})
</script>

<style scoped>
.context-menu {
  position: fixed;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 4px 0;
  z-index: 1000;
  min-width: 120px;
  box-shadow: 0 4px 12px var(--shadow-color);
}

.context-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
}

.context-item:hover {
  background: var(--bg-tertiary);
  color: var(--accent-color);
}

.context-item.danger {
  color: #f56c6c;
}

.context-item.danger:hover {
  background: #fef0f0;
}

.preview-content {
  min-height: 300px;
}
</style>
