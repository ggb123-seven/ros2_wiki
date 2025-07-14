#!/bin/bash

echo "🚀 启动超简化版ROS2 Wiki"
echo "========================="
echo "✅ 无需安装任何依赖包"
echo "✅ 只使用Python标准库"
echo ""

# 启动服务器
python3 simple_server.py &
SERVER_PID=$!

# 等待服务器启动
sleep 2

echo "🌐 启动ngrok隧道..."
./ngrok http 8000 --log=stdout > ngrok_simple.log 2>&1 &
NGROK_PID=$!

# 等待ngrok启动
sleep 3

# 获取公网地址
PUBLIC_URL=""
for i in {1..8}; do
    if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        if tunnel['proto'] == 'https':
            print(tunnel['public_url'])
            break
except:
    pass
")
        if [ -n "$PUBLIC_URL" ]; then
            break
        fi
    fi
    echo "等待ngrok启动... ($i/8)"
    sleep 2
done

echo ""
echo "🎉 网站启动成功！"
echo "=================="
echo "📱 本地访问: http://localhost:8000"
if [ -n "$PUBLIC_URL" ]; then
    echo "🌍 公网访问: $PUBLIC_URL"
else
    echo "⚠️  公网地址获取失败，请手动检查 http://localhost:4040"
fi
echo ""
echo "🔄 服务运行中... (按Ctrl+C停止)"

# 创建停止脚本
cat > stop_simple.sh << 'EOF'
#!/bin/bash
echo "🛑 停止服务..."
pkill -f "simple_server.py" || true
pkill -f "./ngrok" || true
rm -f ngrok_simple.log
echo "✅ 服务已停止"
EOF
chmod +x stop_simple.sh

# 保持运行
trap 'echo ""; echo "🛑 正在停止服务..."; kill $SERVER_PID $NGROK_PID 2>/dev/null || true; rm -f ngrok_simple.log; echo "✅ 服务已停止"; exit 0' INT

wait