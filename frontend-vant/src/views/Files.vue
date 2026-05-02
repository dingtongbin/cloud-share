<template>
  <div class="files-page">
    <!-- 操作工具栏 -->
    <div class="toolbar flex items-center justify-between mb-2" style="gap: 8px;">
      <div class="flex gap-2">
        <van-button size="small" type="primary" icon="upgrade" @click="triggerUpload">上传</van-button>
        <van-button size="small" icon="folder-o" @click="triggerUploadFolder">上传文件夹</van-button>
        <van-button size="small" icon="add-o" @click="showCreateFolder = true">新建文件夹</van-button>
      </div>
      <div class="flex gap-2">
        <van-button
          size="small"
          :type="viewMode === 'grid' ? 'primary' : 'default'"
          @click="viewMode = 'grid'"
        >网格</van-button>
        <van-button
          size="small"
          :type="viewMode === 'list' ? 'primary' : 'default'"
          @click="viewMode = 'list'"
        >列表</van-button>
      </div>
    </div>
    <input ref="fileInput" type="file" multiple hidden @change="handleUploadFiles" />
    <input ref="folderInput" type="file" webkitdirectory multiple hidden @change="handleUploadFolder" />

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
    <van-progress
      v-if="uploading"
      :percentage="uploadPercent"
      :show-pivot="false"
      color="#1989fa"
      style="margin-bottom: 10px;"
    />

    <!-- 网格视图 -->
    <template v-if="viewMode === 'grid'">
      <div class="file-grid">
        <div
          v-for="folder in folders"
          :key="'f-' + folder.id"
          class="file-card"
          @click="navigateTo(folder.file_path)"
          @contextmenu.prevent="showItemActions({ ...folder, _type: 'folder' })"
          @touchstart.passive="onTouchStart($event, folder, 'folder')"
          @touchend="onTouchEnd"
        >
          <div class="file-icon">📁</div>
          <div class="file-name">{{ folder.original_name }}</div>
          <div class="file-size">文件夹</div>
        </div>
        <div
          v-for="file in files"
          :key="file.id"
          class="file-card"
          @click="showItemActions({ ...file, _type: 'file' })"
          @contextmenu.prevent="showItemActions({ ...file, _type: 'file' })"
          @touchstart.passive="onTouchStart($event, file, 'file')"
          @touchend="onTouchEnd"
        >
          <div class="file-icon">{{ getFileIcon(file.original_name) }}</div>
          <div class="file-name">{{ file.original_name }}</div>
          <div class="file-size">{{ formatSize(file.file_size) }}</div>
        </div>
      </div>
    </template>

    <!-- 列表视图 -->
    <template v-else>
      <div
        v-for="item in allItems"
        :key="item._key"
        class="file-list-item"
        @click="onItemClick(item)"
        @contextmenu.prevent="showItemActions(item)"
        @touchstart.passive="onTouchStart($event, item._data, item._type)"
        @touchend="onTouchEnd"
      >
        <div class="file-list-icon">{{ item._type === 'folder' ? '📁' : getFileIcon(item.original_name) }}</div>
        <div class="file-list-info">
          <div class="file-list-name">{{ item.original_name }}</div>
          <div class="file-list-meta">
            {{ item._type === 'folder' ? '文件夹' : formatSize(item.file_size) }}
            <span v-if="item._type === 'file' && item.updated_at"> · {{ formatTime(item.updated_at || item.created_at) }}</span>
          </div>
        </div>
        <div class="file-list-actions">
          <van-icon name="ellipsis" size="20" @click.stop="showItemActions(item)" />
        </div>
      </div>
    </template>

    <!-- 空状态 -->
    <van-empty v-if="!loading && folders.length === 0 && files.length === 0" description="此文件夹为空" />

    <!-- 操作面板 -->
    <van-action-sheet
      v-model:show="showActions"
      :actions="currentActions"
      cancel-text="取消"
      @select="onActionSelect"
    />

    <!-- 创建文件夹 -->
    <van-dialog
      v-model:show="showCreateFolder"
      title="新建文件夹"
      show-cancel-button
      @confirm="createFolder"
    >
      <div style="padding: 16px;">
        <van-field v-model="newFolderName" placeholder="请输入文件夹名称" autofocus />
      </div>
    </van-dialog>

    <!-- 重命名 -->
    <van-dialog
      v-model:show="showRename"
      title="重命名"
      show-cancel-button
      @confirm="doRename"
    >
      <div style="padding: 16px;">
        <van-field v-model="newFileName" placeholder="请输入新文件名" autofocus />
      </div>
    </van-dialog>

    <!-- 创建分享 -->
    <van-popup v-model:show="showShare" position="bottom" :style="{ maxHeight: '80vh' }" round>
      <div class="popup-content">
        <div class="popup-title">创建分享链接</div>
        <van-cell-group inset v-if="!shareResult">
          <van-field label="有效时间">
            <template #input>
              <van-radio-group v-model="shareForm.expire_hours" direction="horizontal">
                <van-radio :name="0">永不过期</van-radio>
                <van-radio :name="1">1小时</van-radio>
                <van-radio :name="24">24小时</van-radio>
                <van-radio :name="168">7天</van-radio>
              </van-radio-group>
            </template>
          </van-field>
          <van-field v-model="shareForm.max_downloads" type="number" label="下载次数" placeholder="0=不限制" />
          <van-field v-model="shareForm.password" label="访问密码" placeholder="留空则无密码" />
          <van-field
            v-model="shareForm.message"
            type="textarea"
            label="分享留言"
            placeholder="给下载者的一段话（可选，最多400字）"
            :maxlength="400"
            show-word-limit
            :autosize="{ minHeight: 60 }"
          />
        </van-cell-group>
        <div v-if="shareResult" style="text-align: center; padding: 16px;">
          <p class="mb-2">分享链接已创建</p>
          <van-field v-model="shareUrl" readonly label="链接" />
          <img v-if="shareQrUrl" :src="shareQrUrl" style="width: 160px; margin-top: 12px;" />
        </div>
        <div style="padding: 16px;">
          <van-button v-if="!shareResult" round block type="primary" @click="doCreateShare">创建</van-button>
          <van-button v-if="shareResult" round block @click="copyShareUrl">复制链接</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 文件预览 -->
    <van-popup v-model:show="showPreview" position="bottom" :style="{ height: '90vh' }" round>
      <div class="popup-content" style="height: 100%; overflow: auto;">
        <div class="popup-title">
          {{ previewFileData?.original_name || '文件预览' }}
          <van-icon name="cross" size="20" @click="showPreview = false" style="float: right;" />
        </div>
        <div v-if="previewData" style="padding: 12px;">
          <template v-if="previewData.type === 'text'">
            <div class="flex justify-between items-center mb-2">
              <span></span>
              <van-button v-if="!editing" size="mini" @click="startEdit">编辑</van-button>
              <div v-else class="flex gap-2">
                <van-button size="mini" type="primary" @click="saveEdit">保存</van-button>
                <van-button size="mini" @click="cancelEdit">取消</van-button>
              </div>
            </div>
            <van-field
              v-if="editing"
              v-model="editContent"
              type="textarea"
              :autosize="{ minHeight: 300 }"
              style="font-family: monospace;"
            />
            <pre v-else class="text-preview">{{ previewData.content }}</pre>
          </template>
          <template v-else-if="previewData.type === 'image'">
            <img :src="previewData.url" style="max-width: 100%; border-radius: 8px;" />
          </template>
          <template v-else-if="previewData.type === 'media'">
            <video v-if="previewData.content_type?.startsWith('video')" :src="previewData.url" controls style="width: 100%;" />
            <audio v-else :src="previewData.url" controls style="width: 100%;" />
          </template>
          <template v-else-if="previewData.type === 'pdf'">
            <iframe :src="previewData.url" style="width: 100%; height: 60vh; border: none;" />
          </template>
          <template v-else>
            <div class="text-center">
              <p class="mb-4">该文件类型不支持在线预览</p>
              <van-button type="primary" @click="downloadFile(previewFileData)">下载文件</van-button>
            </div>
          </template>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, inject, onUnmounted, watch } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import request from '../utils/request'

const currentPath = ref('/')
const folders = ref([])
const files = ref([])
const loading = ref(false)
const viewMode = ref('grid')
const refreshStorage = inject('refreshStorage')

const fileInput = ref()
const folderInput = ref()
const uploading = ref(false)
const uploadPercent = ref(0)

const showCreateFolder = ref(false)
const newFolderName = ref('')

const showRename = ref(false)
const newFileName = ref('')
const renameFileId = ref(null)

const showShare = ref(false)
const shareForm = reactive({
  expire_hours: 0,
  max_downloads: 0,
  password: '',
  message: '',
  file_id: null,
})
const shareResult = ref(false)
const shareUrl = ref('')
const shareQrUrl = ref('')

const showPreview = ref(false)
const previewData = ref(null)
const previewFileData = ref(null)
const editing = ref(false)
const editContent = ref('')
const editingFileId = ref(null)

const showActions = ref(false)
const currentActions = ref([])
const actionItem = ref(null)

let longPressTimer = null

const allItems = computed(() => [
  ...folders.value.map(f => ({ ...f, _type: 'folder', _key: 'f-' + f.id, _data: f })),
  ...files.value.map(f => ({ ...f, _type: 'file', _key: f.id, _data: f })),
])

const pathSegments = computed(() => {
  if (currentPath.value === '/') return []
  return currentPath.value.split('/').filter(Boolean)
})

const buildPath = (index) => '/' + pathSegments.value.slice(0, index + 1).join('/')

const navigateTo = (path) => {
  currentPath.value = path || '/'
  loadFiles()
}

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

const formatTime = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

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
          uploadPercent.value = Math.round(((i + (evt.loaded / (evt.total || 1))) / fileList.length) * 100)
        },
      })
    } catch {
      showToast('上传失败: ' + fileList[i].name)
    }
  }
  uploadPercent.value = 100
  uploading.value = false
  fileInput.value.value = ''
  showToast('上传完成')
  loadFiles()
  refreshStorage?.()
}

const handleUploadFolder = async (e) => {
  const fileList = e.target.files
  if (!fileList.length) return
  uploading.value = true
  uploadPercent.value = 0
  const fd = new FormData()
  for (let i = 0; i < fileList.length; i++) {
    const f = fileList[i]
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
    showToast('文件夹上传完成')
  } catch {
    showToast('文件夹上传失败')
  }
  uploadPercent.value = 100
  uploading.value = false
  folderInput.value.value = ''
  loadFiles()
  refreshStorage?.()
}

const createFolder = async () => {
  if (!newFolderName.value.trim()) {
    showToast('请输入文件夹名称')
    return
  }
  await request.post('/files/folder', { name: newFolderName.value, parent: currentPath.value })
  showToast('文件夹创建成功')
  showCreateFolder.value = false
  newFolderName.value = ''
  loadFiles()
}

const downloadFile = async (file) => {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/api/files/download/' + file.id, {
      headers: { Authorization: 'Bearer ' + token },
    })
    if (!res.ok) {
      showToast('下载失败')
      return
    }
    const blob = await res.blob()
    const disposition = res.headers.get('content-disposition')
    let filename = file.original_name
    if (disposition) {
      const m = disposition.match(/filename[^=]*=\s*"?([^";\n]+)"?/)
      if (m) filename = decodeURIComponent(m[1])
    }
    const u = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = u
    link.download = filename
    link.click()
    URL.revokeObjectURL(u)
  } catch { showToast('下载失败') }
}

const downloadFolder = async (folder) => {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/api/files/download-folder?folder=' + encodeURIComponent(folder.file_path), {
      headers: { Authorization: 'Bearer ' + token },
    })
    if (!res.ok) {
      showToast('下载失败')
      return
    }
    const blob = await res.blob()
    const disposition = res.headers.get('content-disposition')
    let filename = folder.original_name + '.zip'
    if (disposition) {
      const m = disposition.match(/filename[^=]*=\s*"?([^";\n]+)"?/)
      if (m) filename = decodeURIComponent(m[1])
    }
    const u = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = u
    link.download = filename
    link.click()
    URL.revokeObjectURL(u)
  } catch { showToast('下载失败') }
}

const fetchBlobUrl = async (fileId) => {
  const token = localStorage.getItem('token')
  const res = await fetch('/api/files/preview/' + fileId, {
    headers: { Authorization: 'Bearer ' + token },
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
      const res = await request.get('/files/content/' + file.id)
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
    showToast('预览失败')
  }
}

const startEdit = async () => {
  try {
    const res = await request.get('/files/content/' + previewFileData.value.id)
    editContent.value = res.content
    editingFileId.value = previewFileData.value.id
    editing.value = true
  } catch {
    showToast('获取文件内容失败')
  }
}

const saveEdit = async () => {
  try {
    await request.put('/files/content/' + editingFileId.value, { content: editContent.value })
    showToast('保存成功')
    editing.value = false
    previewData.value.content = editContent.value
  } catch {
    showToast('保存失败')
  }
}

const cancelEdit = () => { editing.value = false }

const doRename = async () => {
  if (!newFileName.value.trim()) {
    showToast('请输入新文件名')
    return
  }
  await request.put('/files/rename/' + renameFileId.value, { new_name: newFileName.value })
  showToast('重命名成功')
  showRename.value = false
  loadFiles()
}

const deleteFile = async (file) => {
  await request.delete('/files/' + file.id)
  showToast('文件已删除')
  loadFiles()
  refreshStorage?.()
}

const deleteFolder = async (folder) => {
  const path = folder.file_path.startsWith('/') ? folder.file_path.slice(1) : folder.file_path
  await request.delete('/files/folder/' + path)
  showToast('文件夹已删除')
  loadFiles()
  refreshStorage?.()
}

const doCreateShare = async () => {
  try {
    const res = await request.post('/shares', {
      file_id: shareForm.file_id,
      expire_hours: shareForm.expire_hours || 0,
      max_downloads: parseInt(shareForm.max_downloads) || 0,
      password: shareForm.password || null,
      message: shareForm.message || null,
    })
    const baseUrl = window.location.origin
    shareUrl.value = baseUrl + '/share/' + res.share_code
    shareQrUrl.value = '/api/shares/qrcode-img/' + res.share_code
    shareResult.value = true
    showToast('分享链接创建成功')
  } catch {}
}

const copyShareUrl = () => {
  const text = shareUrl.value
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => showToast('已复制到剪贴板'))
  } else {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    showToast('已复制到剪贴板')
  }
}

const onTouchStart = (e, data, type) => {
  longPressTimer = setTimeout(() => {
    showItemActions({ ...data, _type: type })
  }, 600)
}

const onTouchEnd = () => {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

const showItemActions = (item) => {
  actionItem.value = item
  if (item._type === 'file') {
    currentActions.value = [
      { name: '预览', value: 'preview' },
      { name: '下载', value: 'download' },
      { name: '分享', value: 'share' },
      { name: '重命名', value: 'rename' },
      { name: '删除', color: '#ee0a24', value: 'delete' },
    ]
  } else {
    currentActions.value = [
      { name: '打开', value: 'open' },
      { name: '下载ZIP', value: 'download-folder' },
      { name: '分享', value: 'share-folder' },
      { name: '重命名', value: 'rename-folder' },
      { name: '删除', color: '#ee0a24', value: 'delete-folder' },
    ]
  }
  showActions.value = true
}

const onActionSelect = (action) => {
  showActions.value = false
  const item = actionItem.value
  switch (action.value) {
    case 'preview': previewFile(item); break
    case 'download': downloadFile(item); break
    case 'share':
      shareForm.file_id = item.id
      shareForm.expire_hours = 0
      shareForm.max_downloads = 0
      shareForm.password = ''
      shareForm.message = ''
      shareResult.value = false
      showShare.value = true
      break
    case 'rename':
      renameFileId.value = item.id
      newFileName.value = item.original_name
      showRename.value = true
      break
    case 'delete':
      showConfirmDialog({ title: '确认删除', message: '确定删除文件 "' + item.original_name + '"？' })
        .then(() => deleteFile(item)).catch(() => {})
      break
    case 'open': navigateTo(item.file_path); break
    case 'download-folder': downloadFolder(item); break
    case 'share-folder':
      shareForm.file_id = item.id
      shareForm.expire_hours = 0
      shareForm.max_downloads = 0
      shareForm.password = ''
      shareForm.message = ''
      shareResult.value = false
      showShare.value = true
      break
    case 'rename-folder':
      renameFileId.value = item.id
      newFileName.value = item.original_name
      showRename.value = true
      break
    case 'delete-folder':
      showConfirmDialog({ title: '确认删除', message: '确定删除文件夹 "' + item.original_name + '" 及其所有内容？' })
        .then(() => deleteFolder(item)).catch(() => {})
      break
  }
}

const onItemClick = (item) => {
  if (item._type === 'folder') {
    navigateTo(item.file_path)
  } else {
    showItemActions(item)
  }
}

watch(showPreview, (val) => {
  if (!val) revokePreviewUrl()
})

onMounted(() => { loadFiles() })
</script>

<style scoped>
.files-page { padding-bottom: 20px; }
.popup-content { max-height: 80vh; overflow: auto; }
.popup-title {
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}
.text-preview {
  background: var(--bg-tertiary);
  padding: 12px;
  border-radius: 8px;
  overflow: auto;
  max-height: 50vh;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-primary);
}
</style>
