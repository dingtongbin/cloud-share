# Cloud Share 依赖管理指南

## Python 后端依赖管理

### 查看当前依赖
```bash
cat backend/requirements.txt
```

### 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 添加新依赖
```bash
# 方法1: 直接添加到 requirements.txt
echo "package-name>=version" >> backend/requirements.txt
pip install package-name

# 方法2: 先安装包,再更新文件
pip install package-name
pip freeze > backend/requirements.txt
```

### 更新依赖
```bash
# 更新所有依赖到最新版本
pip install --upgrade -r backend/requirements.txt

# 更新单个包
pip install --upgrade package-name
```

### 冻结当前环境
```bash
pip freeze > backend/requirements.txt
```

---

## Node.js 前端依赖管理

### 桌面端 (frontend)

#### 安装依赖
```bash
cd frontend
npm install
```

#### 添加新依赖
```bash
# 生产依赖
npm install package-name

# 开发依赖
npm install --save-dev package-name
```

#### 更新依赖
```bash
# 更新所有依赖
npm update

# 更新单个包
npm update package-name
```

#### 查看过时包
```bash
npm outdated
```

### 移动端 (frontend-vant)

操作同上,在 `frontend-vant` 目录执行。

---

## 常用命令速查

### Python
```bash
# 检查已安装的包
pip list

# 查看包信息
pip show package-name

# 卸载包
pip uninstall package-name

# 导出依赖
pip freeze > requirements.txt
```

### Node.js
```bash
# 查看已安装的包
npm list

# 查看全局包
npm list -g

# 清理缓存
npm cache clean --force

# 重新安装
rm -rf node_modules package-lock.json
npm install
```

---

## 版本说明

### Python 依赖版本符号
- `>=`: 大于等于指定版本
- `==`: 精确匹配版本
- `~=`: 兼容版本(推荐)
- `<`: 小于指定版本

示例:
```
fastapi>=0.104.0    # 0.104.0 及以上
bcrypt==4.0.1       # 精确 4.0.1
pydantic~=2.5.0     # 2.5.x 系列
```

### Node.js 依赖版本符号
- `^`: 兼容版本(推荐)
- `~`: 补丁版本
- `*`: 任意版本

示例:
```json
{
  "vue": "^3.5.13",   // 3.x.x, x >= 5.13
  "vite": "~6.0.5",   // 6.0.x, x >= 5
  "axios": "*"        // 任意版本
}
```

---

## 注意事项

1. **Python 环境**: 确保使用 Python 3.10+
2. **虚拟环境**: 建议使用 `.venv` 隔离环境
3. **依赖冲突**: 定期检查并解决依赖冲突
4. **锁定文件**: 
   - Python: 使用 `requirements.txt`
   - Node: 使用 `package-lock.json`
5. **生产环境**: 部署前测试所有依赖兼容性

---

## 问题排查

### Python 依赖问题
```bash
# 重新安装 pip
python -m ensurepip --upgrade

# 清除缓存
pip cache purge

# 强制重装
pip install --force-reinstall -r requirements.txt
```

### Node 依赖问题
```bash
# 清除 node_modules
rm -rf node_modules package-lock.json
npm install

# 清除 npm 缓存
npm cache clean --force

# 使用 legacy peer deps
npm install --legacy-peer-deps
```
