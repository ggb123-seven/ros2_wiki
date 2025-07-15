# ROS2 Wiki 云端部署配置指南

## 🚀 支持的云平台

### 1. Render.com (推荐)
- **免费tier**: 支持
- **数据库**: 免费PostgreSQL
- **自动部署**: GitHub集成
- **HTTPS**: 自动配置

### 2. Railway.app
- **免费tier**: $5/月免费额度
- **数据库**: PostgreSQL支持
- **部署**: 一键部署

### 3. Heroku
- **免费tier**: 已停止，付费方案
- **数据库**: PostgreSQL插件
- **部署**: Git推送

## 📋 部署前检查清单

### ✅ 必需文件
- [x] `app.py` - 主应用文件
- [x] `requirements.txt` - Python依赖
- [x] `Procfile` - 进程配置
- [x] `render.yaml` - Render配置
- [x] `runtime.txt` - Python版本
- [x] `.gitignore` - Git忽略文件

### ✅ 功能验证
- [x] 用户认证系统
- [x] 用户管理功能
- [x] 黑名单管理
- [x] 操作审计
- [x] 文档管理
- [x] 搜索功能

## 🔧 环境变量配置

### 必需环境变量
```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:port/dbname
FLASK_ENV=production
```

### 可选环境变量
```bash
MIN_PASSWORD_LENGTH=8
REQUIRE_SPECIAL_CHARS=True
MAX_UPLOAD_SIZE=16777216
```

## 📦 部署步骤

### Render.com 部署

1. **推送到GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **连接Render**
   - 访问 [render.com](https://render.com)
   - 连接GitHub仓库
   - 选择Web Service

3. **配置设置**
   - **Name**: ros2-wiki
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

4. **环境变量**
   - 添加必需的环境变量
   - 数据库会自动配置

### Railway.app 部署

1. **连接Railway**
   - 访问 [railway.app](https://railway.app)
   - 从GitHub部署

2. **添加数据库**
   - 添加PostgreSQL服务
   - 环境变量自动配置

### 手动部署

1. **服务器准备**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

2. **应用部署**
   ```bash
   git clone your-repo-url
   cd ros2_wiki
   pip3 install -r requirements.txt
   gunicorn --bind 0.0.0.0:8000 app:app
   ```

## 🔒 安全配置

### 生产环境安全
- 使用强SECRET_KEY
- 启用HTTPS
- 配置防火墙
- 定期更新依赖

### 数据库安全
- 使用环境变量存储凭据
- 启用SSL连接
- 定期备份数据

## 📊 监控和维护

### 日志监控
- 应用日志
- 错误追踪
- 性能监控

### 定期维护
- 依赖更新
- 安全补丁
- 数据库优化

## 🆘 故障排除

### 常见问题
1. **数据库连接失败**
   - 检查DATABASE_URL
   - 验证网络连接

2. **静态文件404**
   - 检查静态文件路径
   - 配置Web服务器

3. **权限错误**
   - 检查文件权限
   - 验证用户权限

### 调试命令
```bash
# 检查应用状态
curl -I https://your-app.onrender.com

# 查看日志
heroku logs --tail  # Heroku
# 或在Render控制台查看

# 测试数据库连接
python -c "import psycopg2; print('DB OK')"
```

## 📞 支持

如遇部署问题：
1. 检查日志文件
2. 验证环境变量
3. 测试本地运行
4. 查看平台文档
