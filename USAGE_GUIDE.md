# ROS2 Wiki 项目使用指南

## 🚀 **项目概述**

ROS2 Wiki是一个功能完整的技术文档网站，包含企业级安全、智能搜索、内容管理和用户权限管理功能。

### **✅ 已完成功能**
- 🔒 **企业级安全** (输入验证、XSS防护、CSRF保护、密码强度验证)
- 🔍 **智能搜索** (全文搜索、相关性排序、搜索建议、热门词汇)
- 📝 **内容管理系统** (Markdown编辑、文件上传、分类管理、统计分析)
- 👥 **用户权限管理** (用户CRUD、角色分配、权限控制、活动监控)
- 🏗️ **蓝图架构** (模块化设计、应用工厂、错误处理、可扩展结构)
- 🚀 **统一部署** (Docker编排、多环境配置、一键部署、自动备份)

## 🎯 **快速开始**

### **方案1：测试环境 (当前可用)**
```bash
# 启动测试服务器
python3 test_server.py

# 访问地址
http://localhost:8000
```

### **方案2：Docker环境 (推荐)**
```bash
# 前提：已安装Docker Desktop

# 开发环境
./deploy.sh dev

# 生产环境
./deploy.sh prod

# 查看状态
./deploy.sh --status
```

### **方案3：Render部署 (生产)**
```bash
# 代码已推送到GitHub
# Render会自动部署
https://github.com/ggb123-seven/ros2_wiki
```

## 🔧 **环境配置**

### **开发环境**
```bash
# 环境文件：.env.dev
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///dev_ros2_wiki.db
```

### **生产环境**
```bash
# 环境文件：.env.prod
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=CHANGE-THIS-TO-RANDOM-SECRET-KEY
DATABASE_URL=postgresql://user:pass@host/db
```

## 📦 **功能模块**

### **1. 安全模块 (app/security.py)**
```python
from app.security import (
    PasswordValidator,      # 密码强度验证
    InputValidator,         # 输入清理验证
    admin_required,         # 管理员权限装饰器
    validate_csrf_token,    # CSRF保护
    rate_limit             # 请求频率限制
)
```

### **2. 搜索功能 (app/search.py)**
```python
# 搜索API
GET /search/api?q=关键词&page=1&per_page=10

# 搜索建议
GET /search/suggestions?q=关键词

# 热门搜索
GET /search/popular
```

### **3. 内容管理 (app/cms.py)**
```python
# 管理后台
/admin/                    # 仪表板
/admin/cms/documents       # 文档管理
/admin/cms/upload          # 文件上传
/admin/cms/preview         # Markdown预览
```

### **4. 用户权限 (app/permissions.py)**
```python
# 用户管理
/admin/users/              # 用户列表
/admin/users/new           # 新建用户
/admin/users/{id}/edit     # 编辑用户
/admin/users/{id}/delete   # 删除用户
```

### **5. API接口 (app/api.py)**
```python
# 文档API
GET /api/documents         # 文档列表
GET /api/documents/{id}    # 文档详情
POST /api/documents        # 创建文档

# 统计API
GET /api/stats             # 统计信息
GET /api/health            # 健康检查
```

## 🛠️ **部署选项**

### **Docker部署**
```bash
# 开发环境
./deploy.sh dev

# 生产环境
./deploy.sh prod --force

# 查看日志
./deploy.sh --logs

# 数据备份
./deploy.sh --backup

# 清理资源
./deploy.sh --cleanup
```

### **Render部署**
1. 连接GitHub仓库
2. 配置环境变量
3. 自动部署

### **手动部署**
```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑.env文件

# 启动应用
python run.py
```

## 📊 **监控和维护**

### **日志查看**
```bash
# Docker日志
./deploy.sh --logs

# 应用日志
tail -f logs/ros2_wiki.log

# Nginx日志
tail -f logs/nginx/access.log
```

### **健康检查**
```bash
# API健康检查
curl http://localhost:5000/api/health

# 服务状态
./deploy.sh --status
```

### **数据备份**
```bash
# 创建备份
./deploy.sh --backup

# 恢复备份
./deploy.sh --restore backup-file.sql
```

## 🔍 **故障排除**

### **常见问题**

**1. 依赖安装失败**
```bash
# 检查Python版本
python --version

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

**2. 数据库连接失败**
```bash
# 检查环境变量
echo $DATABASE_URL

# 重新初始化数据库
python -c "from app import create_app; create_app().app_context().push()"
```

**3. Docker启动失败**
```bash
# 检查Docker状态
docker --version
docker-compose --version

# 重新构建
./deploy.sh dev --force
```

## 🎯 **下一步开发**

### **功能增强**
- [ ] 实时通知系统
- [ ] 邮件订阅功能
- [ ] 多语言支持
- [ ] 主题定制
- [ ] 移动端优化

### **性能优化**
- [ ] Redis缓存优化
- [ ] 数据库索引优化
- [ ] CDN集成
- [ ] 图片压缩
- [ ] 懒加载实现

### **运维增强**
- [ ] 监控告警
- [ ] 自动扩容
- [ ] 蓝绿部署
- [ ] 灰度发布
- [ ] 故障恢复

## 📞 **支持和贡献**

- **GitHub**: https://github.com/ggb123-seven/ros2_wiki
- **文档**: 查看项目中的markdown文件
- **问题反馈**: 通过GitHub Issues提交
- **功能请求**: 欢迎提交Pull Request

---

*最后更新: 2025-07-09*
*版本: 2.0.0*
*作者: 与Claude Code协作开发*