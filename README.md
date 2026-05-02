# Cloud Share - 个人文件分发系统

一个基于 FastAPI + Vue 3 的轻量级个人文件分发系统，专注于简洁高效的文件分享与分发功能。

> **注意**: 本项目代码主体部分由 AI 辅助生成，作者 dingtongbin 负责项目架构设计、功能规划和代码审查。

## ✨ 项目理念

在云存储日益强大的今天，Cloud Share 回归文件分发的本质——**简单、快速、私密**。这不是一个面向大众的网盘，而是为个人和小团队设计的轻量级文件分发工具。

### 核心特性

### 后端功能
- 🔐 **用户认证**: JWT Token 认证，支持管理员和普通用户
- 📁 **文件管理**: 上传、下载、预览、删除、重命名、文件夹操作
- 🔗 **文件分享**: 生成分享链接，支持密码保护、下载次数限制、过期时间
- 📊 **空间管理**: 用户存储配额管理，实时显示使用情况
- 👨‍💼 **后台管理**: 用户管理、分享记录、下载日志、系统统计
- 🖼️ **文件预览**: 支持图片、视频、文本文件在线预览
- 📦 **批量操作**: 支持文件夹打包下载、批量上传

### 前端功能
- 💻 **桌面端**: 基于 Element Plus 的响应式管理界面
- 📱 **移动端**: 基于 Vant 的移动适配界面
- 🎨 **现代化 UI**: 简洁美观的深色科技风格设计
- ⚡ **快速响应**: Vite 构建，热更新开发体验

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **数据库**: SQLAlchemy 2.0 + SQLite
- **认证**: python-jose (JWT)
- **文件处理**: aiofiles, Pillow, qrcode
- **服务器**: Uvicorn

### 前端
- **框架**: Vue 3.5 + Vite 6
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **UI 组件**: 
  - 桌面端: Element Plus 2.9
  - 移动端: Vant 4.9
- **HTTP 客户端**: Axios
- **二维码**: qrcode

## 📋 项目结构

```
cloud-driver/
├── backend/                 # 后端服务 (端口 29000)
│   ├── app/
│   │   ├── config.py       # 应用配置
│   │   ├── database.py     # 数据库连接
│   │   ├── models/         # 数据模型
│   │   ├── routes/         # API 路由
│   │   │   ├── auth.py    # 认证接口
│   │   │   ├── files.py   # 文件管理接口
│   │   │   ├── shares.py  # 分享接口
│   │   │   ├── admin.py   # 管理接口
│   │   │   └── api.py     # 其他接口
│   │   ├── schemas/        # Pydantic 模型
│   │   └── utils/          # 工具函数
│   ├── database/           # 数据库文件目录
│   ├── files/             # 用户上传文件存储
│   ├── main.py            # 后端入口
│   └── requirements.txt   # Python 依赖
│
├── frontend/               # 桌面端前端 (端口 29001)
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态
│   │   └── utils/         # 工具函数
│   ├── package.json       # Node 依赖
│   └── vite.config.js     # Vite 配置
│
├── frontend-vant/          # 移动端前端 (端口 29002)
│   ├── src/
│   └── package.json
│
├── files/                  # 根目录文件存储(备用)
└── .gitignore             # Git 忽略配置
```

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- npm 或 yarn

### 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务 (默认端口 29000)
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 29000 --reload
```

启动后访问：
- 🌐 **API 文档**: http://localhost:29000/docs
- 💻 **桌面端**: http://localhost:29001
- 📱 **移动端**: http://localhost:29002

### 前端启动

```bash
# 桌面端 (端口 29001)
cd frontend
npm install
npm run dev

# 移动端 (端口 29002)
cd frontend-vant
npm install
npm run dev
```

### 默认账户
- **管理员**: `admin` / `admin123`
- 首次启动会自动创建管理员账户

## 📝 API 文档

启动后端后访问: `http://localhost:29000/docs`

主要接口:
- `POST /api/auth/login` - 用户登录
- `GET /api/files/list` - 列出文件
- `POST /api/files/upload` - 上传文件
- `GET /api/files/download/{file_id}` - 下载文件
- `POST /api/shares` - 创建分享
- `GET /api/shares/access/{code}` - 访问分享

## ⚙️ 配置说明

编辑 `backend/app/config.py`:

```python
# 数据库
DATABASE_URL = "sqlite:///./database/cloud.db"

# JWT 密钥 (生产环境请修改)
SECRET_KEY = "your-secret-key"

# 服务器
HOST = "0.0.0.0"
PORT = 29000

# 默认管理员
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# 默认配额 (10GB)
DEFAULT_QUOTA = 10 * 1024 * 1024 * 1024
```

## 📦 依赖管理

### Python 依赖
```bash
# 查看当前依赖
cat backend/requirements.txt

# 添加新依赖
echo "package-name>=version" >> backend/requirements.txt
pip install -r backend/requirements.txt

# 冻结当前环境
pip freeze > backend/requirements.txt
```

### Node 依赖
```bash
# 桌面端
cd frontend
npm install <package-name>

# 移动端
cd frontend-vant
npm install <package-name>
```

## 🔧 开发说明

### 数据库迁移
项目使用 SQLAlchemy ORM,修改模型后自动同步:
```python
# backend/app/database.py
Base.metadata.create_all(bind=engine)
```

### 文件存储
- 用户上传的文件存储在 `backend/files/{user_id}/` 目录
- 数据库记录文件的元信息和路径映射

### 分享机制
- 分享码: 8位随机字符串
- 支持密码保护、下载次数限制、过期时间
- 分享只能取消不能删除(保留记录)

## 📄 许可证

本项目采用 Apache License 2.0 开源许可证。

Copyright 2026 dingtongbin

详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 🔗 相关链接

- **GitHub**: https://github.com/dingtongbin/cloud-share
- **作者**: [@dingtongbin](https://github.com/dingtongbin)

---

**注意**: 生产环境部署时请务必修改默认密码和 SECRET_KEY!
