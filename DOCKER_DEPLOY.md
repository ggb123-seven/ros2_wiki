# 🐳 Docker本地部署指南

## 📋 **Docker安装步骤 (WSL2)**

### **步骤1：下载Docker Desktop**
1. 访问：https://docs.docker.com/desktop/windows/install/
2. 下载 "Docker Desktop for Windows"
3. 运行安装程序 (需要管理员权限)

### **步骤2：启用WSL2集成**
1. 启动Docker Desktop
2. 进入 **Settings** → **General**
3. 确保勾选 "Use WSL 2 based engine"
4. 进入 **Settings** → **Resources** → **WSL Integration**
5. 启用 "Enable integration with my default WSL distro"
6. 启用 "Ubuntu-24.04" (您的当前发行版)

### **步骤3：验证安装**
```bash
# 检查Docker版本
docker --version

# 检查Docker Compose版本
docker-compose --version

# 测试Docker运行
docker run hello-world
```

### **步骤4：部署ROS2 Wiki**
```bash
# 进入项目目录
cd /home/sevenseven/ros2_wiki

# 开发环境部署
./deploy.sh dev

# 或者生产环境部署
./deploy.sh prod
```

## 🚀 **Docker部署优势**

### **✅ 优点**
- 🔧 **环境一致** - 开发生产环境完全一致
- 🏠 **本地控制** - 完全控制部署环境
- 💰 **完全免费** - 无任何使用限制
- 🔄 **快速迭代** - 本地开发测试便捷
- 📦 **完整功能** - 包含PostgreSQL、Redis、Nginx
- 🛠️ **调试友好** - 可以直接查看日志和调试

### **⚠️ 注意事项**
- 💻 **资源消耗** - 占用本地计算资源
- 🌐 **访问限制** - 仅本地网络可访问
- 🔧 **维护成本** - 需要手动管理更新

## 🎯 **部署完成后功能**

### **服务清单**
- **主应用**: http://localhost:5000
- **数据库**: PostgreSQL (端口5432)
- **缓存**: Redis (端口6379)
- **代理**: Nginx (端口80/443)
- **监控**: 健康检查和日志

### **管理命令**
```bash
# 查看状态
./deploy.sh --status

# 查看日志
./deploy.sh --logs

# 数据备份
./deploy.sh --backup

# 清理资源
./deploy.sh --cleanup
```

## 🔧 **故障排除**

### **Docker安装问题**
1. 确保Windows版本支持WSL2
2. 启用虚拟化功能
3. 更新WSL2内核

### **部署失败**
1. 检查Docker服务状态
2. 验证端口占用情况
3. 查看部署日志

## 📊 **性能监控**
```bash
# 资源使用情况
docker stats

# 容器状态
docker ps

# 日志监控
docker logs -f ros2-wiki-app
```