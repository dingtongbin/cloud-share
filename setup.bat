@echo off
chcp 65001 >nul
echo ========================================
echo   Cloud Share 本地开发环境启动
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python,请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js,请先安装 Node.js 18+
    pause
    exit /b 1
)

echo [1/4] 检查后端依赖...
cd backend
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [警告] 后端依赖安装失败,请手动执行: pip install -r requirements.txt
) else (
    echo [完成] 后端依赖已就绪
)
deactivate
cd ..

echo.
echo [2/4] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo 安装桌面端依赖...
    call npm install
    if errorlevel 1 (
        echo [警告] 桌面端依赖安装失败
    ) else (
        echo [完成] 桌面端依赖已就绪
    )
) else (
    echo [完成] 桌面端依赖已存在
)
cd ..

cd frontend-vant
if not exist "node_modules" (
    echo 安装移动端依赖...
    call npm install
    if errorlevel 1 (
        echo [警告] 移动端依赖安装失败
    ) else (
        echo [完成] 移动端依赖已就绪
    )
) else (
    echo [完成] 移动端依赖已存在
)
cd ..

echo.
echo ========================================
echo   环境检查完成!
echo ========================================
echo.
echo 启动服务:
echo   后端:   cd backend ^&^& python main.py  (端口 29000)
echo   桌面端: cd frontend ^&^& npm run dev     (端口 29001)
echo   移动端: cd frontend-vant ^&^& npm run dev
echo.
echo 默认管理员账户: admin / admin123
echo.
echo GitHub: https://github.com/dingtongbin/cloud-share
echo.
pause
