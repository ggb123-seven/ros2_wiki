@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 🚀 ROS2 Wiki Windows 自动化部署脚本
REM 一键部署到多个云平台

echo ================================
echo 🚀 ROS2 Wiki 自动化部署
echo ================================
echo 管理员账户: ssss / ssss123
echo 邮箱: seventee_0611@qq.com
echo.

REM 检查必需的工具
echo [INFO] 检查部署环境...

REM 检查Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git 未安装，请先安装 Git
    pause
    exit /b 1
)
echo [INFO] ✅ Git 已安装

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装，请先安装 Python
    pause
    exit /b 1
)
echo [INFO] ✅ Python 已安装

REM 检查curl
curl --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] curl 未安装，部分测试功能可能不可用
) else (
    echo [INFO] ✅ curl 已安装
)

echo.
echo ================================
echo 验证项目配置
echo ================================

REM 检查必需文件
set "files=app.py requirements.txt render.yaml Procfile cloud_init_db.py"
for %%f in (%files%) do (
    if exist "%%f" (
        echo [INFO] ✅ %%f 存在
    ) else (
        echo [ERROR] ❌ %%f 不存在
        pause
        exit /b 1
    )
)

REM 检查环境变量配置
findstr /C:"ADMIN_USERNAME.*ssss" render.yaml >nul
if errorlevel 1 (
    echo [ERROR] ❌ 管理员配置错误
    pause
    exit /b 1
) else (
    echo [INFO] ✅ 管理员配置正确
)

echo.
echo ================================
echo 运行本地测试
echo ================================

REM 安装依赖
echo [INFO] 安装Python依赖...
pip install -r requirements.txt >nul 2>&1

REM 设置环境变量
set AUTO_CREATE_ADMIN=true
set ADMIN_USERNAME=ssss
set ADMIN_EMAIL=seventee_0611@qq.com
set ADMIN_PASSWORD=ssss123

REM 测试数据库初始化
echo [INFO] 测试数据库初始化...
python -c "from cloud_init_db import init_cloud_database; import sys; success = init_cloud_database(); print('✅ 数据库初始化测试通过!' if success else '❌ 数据库测试失败!'); sys.exit(0 if success else 1)"
if errorlevel 1 (
    echo [ERROR] 数据库初始化测试失败
    pause
    exit /b 1
)

REM 测试管理员账户
echo [INFO] 测试管理员账户创建...
python -c "import sqlite3; from werkzeug.security import check_password_hash; conn = sqlite3.connect('ros2_wiki.db'); cursor = conn.cursor(); cursor.execute('SELECT username, password_hash, is_admin FROM users WHERE username = ?', ('ssss',)); user = cursor.fetchone(); exit(0 if user and user[2] and check_password_hash(user[1], 'ssss123') else 1)"
if errorlevel 1 (
    echo [ERROR] 管理员账户测试失败
    pause
    exit /b 1
)

echo [INFO] ✅ 所有本地测试通过!

echo.
echo ================================
echo 推送代码到GitHub
echo ================================

REM 检查Git状态
git status --porcelain >nul 2>&1
if not errorlevel 1 (
    for /f %%i in ('git status --porcelain') do (
        echo [INFO] 发现未提交的更改，正在提交...
        git add .
        git commit -m "🚀 Auto deployment: %date% %time%"
        goto :push
    )
)
echo [INFO] 代码已是最新状态

:push
REM 推送到远程仓库
echo [INFO] 推送到GitHub...
git push origin main
if errorlevel 1 (
    echo [ERROR] 推送失败，请检查网络连接和权限
    pause
    exit /b 1
)
echo [INFO] ✅ 代码已推送到GitHub

echo.
echo ================================
echo 选择部署平台
echo ================================
echo 1. Render.com (推荐)
echo 2. Railway.app
echo 3. 两者都部署
echo.

set /p choice="请选择 (1/2/3): "

if "%choice%"=="1" goto :render
if "%choice%"=="2" goto :railway
if "%choice%"=="3" goto :both
echo [ERROR] 无效选择
pause
exit /b 1

:render
echo.
echo ================================
echo 部署到 Render.com
echo ================================
echo [INFO] 📋 Render.com 部署说明:
echo 1. 访问 https://render.com
echo 2. 连接GitHub仓库: ggb123-seven/ros2_wiki
echo 3. 选择 Web Service
echo 4. Render会自动读取 render.yaml 配置
echo 5. 等待部署完成
echo.
echo 🔑 管理员登录信息:
echo    用户名: ssss
echo    密码: ssss123
echo    邮箱: seventee_0611@qq.com
echo.

set /p render_configured="是否已在Render.com上配置部署? (y/n): "
if /i "%render_configured%"=="y" (
    echo [INFO] ✅ Render.com 部署已配置
) else (
    echo [WARNING] 请手动在Render.com上配置部署
)
goto :verify

:railway
echo.
echo ================================
echo 部署到 Railway.app
echo ================================
echo [INFO] 📋 Railway.app 部署说明:
echo 1. 访问 https://railway.app
echo 2. 选择 'Deploy from GitHub repo'
echo 3. 选择仓库: ggb123-seven/ros2_wiki
echo 4. 添加PostgreSQL数据库服务
echo 5. 设置环境变量:
echo    ADMIN_USERNAME=ssss
echo    ADMIN_EMAIL=seventee_0611@qq.com
echo    ADMIN_PASSWORD=ssss123
echo    AUTO_CREATE_ADMIN=true
echo.

set /p railway_configured="是否已在Railway.app上配置部署? (y/n): "
if /i "%railway_configured%"=="y" (
    echo [INFO] ✅ Railway.app 部署已配置
) else (
    echo [WARNING] 请手动在Railway.app上配置部署
)
goto :verify

:both
call :render
call :railway
goto :verify

:verify
echo.
echo ================================
echo 部署后验证
echo ================================
echo 🔍 请验证以下功能:
echo 1. 访问登录页面: /login
echo 2. 使用管理员账户登录: ssss / ssss123
echo 3. 访问管理后台: /admin_dashboard
echo 4. 测试用户管理: /admin/users/
echo 5. 检查调试端点: /debug/admin
echo.
echo 🛠️ 如果遇到问题，请使用调试工具:
echo python cloud_login_debug.py https://your-app.onrender.com
echo.
echo 📞 故障排查指南:
echo 查看 CLOUD_ADMIN_RECOVERY_GUIDE.md
echo.

echo ================================
echo 🎉 部署完成!
echo ================================
echo [INFO] 您的ROS2 Wiki现在已部署到云端!
echo [INFO] 管理员账户: ssss / ssss123
echo.

pause
