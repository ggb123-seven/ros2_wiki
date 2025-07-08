# 🔄 ROS2 Wiki - ngrok 自动重连解决方案

## 问题描述
- ngrok 免费版每8小时自动断连
- 每次重连公网地址都会变化
- 需要手动重启很麻烦

## 解决方案
我们创建了一个自动重连脚本，可以：
- ✅ 自动监控 ngrok 连接状态
- ✅ 断连后自动重启服务
- ✅ 记录连接日志
- ✅ 支持优雅停止

## 使用方法

### 1. 启动自动重连服务
```bash
./auto_restart_ngrok.sh
```

### 2. 停止自动重连服务
```bash
# 方法1：按 Ctrl+C 停止当前运行的服务
# 方法2：使用停止脚本
./stop_auto_restart.sh
```

### 3. 查看服务状态
```bash
# 查看自动重连日志
tail -f auto_restart.log

# 查看ngrok详细日志
tail -f ngrok_auto.log
```

## 功能特点

### 🔄 自动重连
- 每30秒检查一次进程状态
- ngrok断连后5秒内自动重启
- 无需手动干预

### 📊 日志记录
- `auto_restart.log` - 重连历史记录
- `ngrok_auto.log` - ngrok详细日志
- 记录每次连接的公网地址

### 🛡️ 容错处理
- Flask应用异常也会自动重启
- 启动失败会自动重试
- 支持优雅停止

### 📱 实时显示
- 显示当前公网地址
- 显示重连次数
- 显示运行状态

## 输出示例

```
🔄 ROS2 Wiki - ngrok 自动重连启动器
=====================================

🚀 第 1 次启动 (2025-07-07 15:30:00)
===============================
🐍 启动Flask应用...
✅ Flask应用启动成功 (PID: 12345)
🌐 启动ngrok隧道...
✅ ngrok隧道建立成功
🌍 公网地址: https://abc123.ngrok.io

🎉 服务运行中！
===============
📱 本地访问: http://localhost:5000
🌍 公网访问: https://abc123.ngrok.io
📊 ngrok面板: http://localhost:4040

📋 默认账户：
   管理员: admin / admin123
   用户: ros2_learner / user123

💡 提示：
   - 免费版ngrok约8小时后自动重连
   - 每次重连公网地址会变化
   - 按Ctrl+C停止服务
```

## 注意事项

1. **公网地址变化**
   - 每次重连后公网地址会改变
   - 需要重新分享新的地址给其他人

2. **资源占用**
   - 脚本会持续运行在后台
   - 建议在不需要时停止服务

3. **网络环境**
   - 需要稳定的网络连接
   - 如果本地网络不稳定，重连可能会更频繁

## 进阶配置

如果你需要更稳定的解决方案，建议：

1. **升级ngrok付费版** - 无时间限制
2. **使用Cloudflare Tunnel** - 完全免费，更稳定
3. **自建VPS + frp** - 完全控制

## 故障排除

### 问题1：脚本无法启动
```bash
# 检查文件权限
ls -la auto_restart_ngrok.sh
# 如果没有执行权限，运行：
chmod +x auto_restart_ngrok.sh
```

### 问题2：ngrok认证失败
```bash
# 重新配置ngrok token
./setup_ngrok_simple.sh
```

### 问题3：Flask启动失败
```bash
# 检查Python依赖
pip3 install -r requirements.txt
# 检查数据库
python3 init_sample_data.py
```