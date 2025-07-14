#!/bin/bash

# ROS2 Wiki - 停止自动重连脚本

echo "🛑 停止ROS2 Wiki自动重连服务..."

# 停止所有相关进程
pkill -f "auto_restart_ngrok.sh" || true
pkill -f "python3 app.py" || true
pkill -f "./ngrok" || true

# 清理日志文件
rm -f ngrok_auto.log
rm -f auto_restart.log

echo "✅ 所有服务已停止"
echo "📊 如需查看历史日志，请检查 auto_restart.log 文件"