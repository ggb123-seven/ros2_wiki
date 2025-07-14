#!/bin/bash

# ROS2 Wiki - 一键启动公网访问脚本

set -e

echo "🚀 启动ROS2 Wiki公网访问"
echo "========================="

# 检查ngrok是否安装
if ! command -v ngrok >/dev/null 2>&1; then
    echo "❌ ngrok未安装，请先运行: ./setup_ngrok.sh"
    exit 1
fi

# 检查数据库
if [ ! -f "ros2_wiki.db" ]; then
    echo "📦 初始化数据库..."
    python3 init_sample_data.py
fi

# 检查端口是否被占用
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口5000已被占用，正在停止之前的进程..."
    pkill -f "python3 app.py" || true
    sleep 2
fi

echo "🐍 启动Flask应用..."
python3 app.py &
FLASK_PID=$!

# 等待Flask启动
sleep 3

# 检查Flask是否成功启动
if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo "❌ Flask启动失败"
    exit 1
fi

echo "🌐 启动ngrok隧道..."
echo "正在连接到ngrok服务器..."

# 启动ngrok并捕获输出
ngrok http 5000 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

# 等待ngrok启动
sleep 5

# 获取公网地址
PUBLIC_URL=""
for i in {1..10}; do
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
    echo "等待ngrok启动... ($i/10)"
    sleep 2
done

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ 获取公网地址失败，请检查ngrok配置"
    echo "查看ngrok日志:"
    tail -10 ngrok.log
    kill $FLASK_PID $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 网站已成功启动！"
echo "===================="
echo "📱 本地访问: http://localhost:5000"
echo "🌍 公网访问: $PUBLIC_URL"
echo ""
echo "📋 默认账户："
echo "   管理员: admin / admin123"
echo "   用户: ros2_learner / user123"
echo ""
echo "📊 ngrok监控面板: http://localhost:4040"
echo ""
echo "⚠️  提示："
echo "   - 免费版ngrok在8小时后会断开连接"
echo "   - 每次重启公网地址会变化"
echo "   - 按Ctrl+C停止服务"
echo ""

# 创建停止脚本
cat > stop_public.sh << 'EOF'
#!/bin/bash
echo "🛑 停止ROS2 Wiki服务..."
pkill -f "python3 app.py" || true
pkill -f "ngrok" || true
rm -f ngrok.log
echo "✅ 服务已停止"
EOF
chmod +x stop_public.sh

echo "💡 使用 ./stop_public.sh 停止服务"
echo ""

# 保持脚本运行
trap 'echo ""; echo "🛑 正在停止服务..."; kill $FLASK_PID $NGROK_PID 2>/dev/null || true; rm -f ngrok.log; echo "✅ 服务已停止"; exit 0' INT

echo "🔄 服务运行中... (按Ctrl+C停止)"
wait