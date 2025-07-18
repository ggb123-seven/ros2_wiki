
# Render平台部署指令

## 1. 登录Render Dashboard
访问: https://dashboard.render.com
使用GitHub账户登录

## 2. 创建Web Service
1. 点击 "New" -> "Web Service"
2. 连接GitHub仓库: ggb123-seven/ros2_wiki
3. 选择分支: main

## 3. 配置Web Service
Name: ros2-wiki-enterprise
Environment: Python 3
Region: Oregon (US West)
Branch: main
Root Directory: (留空)

Build Command:
pip install -r requirements_render.txt
python cloud_init_db.py

Start Command:
gunicorn app_render:app --bind=0.0.0.0:$PORT --workers=2 --timeout=60

## 4. 创建PostgreSQL数据库
1. 点击 "New" -> "PostgreSQL"
2. 配置:
   - Database Name: ros2-wiki-db
   - Database: ros2_wiki
   - User: ros2_wiki_user
   - Region: Oregon (US West)
   - Plan: Starter (Free)

## 5. 配置环境变量
在Web Service中添加以下环境变量:

SECRET_KEY=3092b9fbcd9523417c2871c8d3b5410cca586856627bc323f4054c5f8f4297f4
DATABASE_URL=[从PostgreSQL服务自动连接]
FLASK_ENV=production
RENDER=true
MIN_PASSWORD_LENGTH=12
REQUIRE_SPECIAL_CHARS=True
ADMIN_USERNAME=admin
ADMIN_EMAIL=seventee_0611@qq.com
ADMIN_PASSWORD=IlukRJovZ05Tyx$b
AUTO_CREATE_ADMIN=true
CSRF_ENABLED=True
SESSION_COOKIE_SECURE=True

## 6. 部署
点击 "Create Web Service" 开始部署
等待5-10分钟完成部署

## 7. 测试
部署完成后，使用以下命令测试:
python test_render_deployment.py https://your-app.onrender.com
