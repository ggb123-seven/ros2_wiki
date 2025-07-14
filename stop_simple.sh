#!/bin/bash
echo "🛑 停止服务..."
pkill -f "simple_server.py" || true
pkill -f "./ngrok" || true
rm -f ngrok_simple.log
echo "✅ 服务已停止"
