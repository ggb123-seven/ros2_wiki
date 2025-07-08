# ROS2 Wiki 部署指南

## 🚀 一键公网访问

### 方法1：自动化配置（推荐）

```bash
# 1. 首次配置
./setup_ngrok.sh

# 2. 启动公网访问
./start_public.sh

# 3. 停止服务
./stop_public.sh
```

### 方法2：手动配置

```bash
# 1. 注册ngrok账号
# 访问 https://dashboard.ngrok.com/signup

# 2. 获取authtoken
# 访问 https://dashboard.ngrok.com/get-started/your-authtoken

# 3. 配置ngrok
ngrok config add-authtoken YOUR_TOKEN

# 4. 启动应用
python3 app.py &

# 5. 启动隧道
ngrok http 5000
```

## 🛠️ 系统服务（可选）

如果您希望网站开机自启动：

```bash
# 安装系统服务
./install_service.sh

# 启动服务
sudo systemctl start ros2-wiki
sudo systemctl start ros2-wiki-ngrok

# 设置开机自启
sudo systemctl enable ros2-wiki ros2-wiki-ngrok
```

## 📋 配置说明

### 1. 获取ngrok token步骤

1. 访问 https://dashboard.ngrok.com/signup
2. 使用Google/GitHub账号注册（免费）
3. 访问 https://dashboard.ngrok.com/get-started/your-authtoken
4. 复制您的authtoken

### 2. 免费版限制

- 每月20,000次请求
- 同时只能有1个隧道
- 8小时后自动断开
- 每次重启URL会变化

### 3. 升级方案

如需稳定服务，建议：
- ngrok付费版（$8/月）
- 云服务器部署
- 其他内网穿透工具

## 🌐 访问地址

启动后您会看到类似地址：
- 本地: http://localhost:5000
- 公网: https://abc123.ngrok.io

## 🔧 故障排除

### 常见问题

1. **ngrok启动失败**
   ```bash
   # 检查token配置
   ngrok config check
   
   # 重新配置token
   ngrok config add-authtoken YOUR_TOKEN
   ```

2. **端口占用**
   ```bash
   # 查找占用进程
   lsof -i :5000
   
   # 杀死进程
   pkill -f "python3 app.py"
   ```

3. **数据库错误**
   ```bash
   # 重新初始化数据库
   rm ros2_wiki.db
   python3 init_sample_data.py
   ```

### 查看日志

```bash
# 查看ngrok日志
tail -f ngrok.log

# 查看系统服务日志
sudo journalctl -u ros2-wiki -f
```

## 📱 默认账户

- 管理员: admin / admin123
- 用户: ros2_learner / user123

## 🔒 安全建议

1. 修改默认密码
2. 使用HTTPS（ngrok免费版已包含）
3. 定期备份数据库
4. 监控访问日志

## 🆘 获取帮助

如有问题，请检查：
1. 网络连接
2. 防火墙设置
3. ngrok配置
4. Python依赖

联系方式：通过GitHub Issues反馈问题