#!/usr/bin/bash

# ROS2 Wiki - ngrok 自动重连脚本
# 解决ngrok免费版8小时断连问题

set -e

echo "🔄 ROS2 Wiki - ngrok 自动重连启动器"
echo "====================================="

# 检查依赖
if [ ! -f "./ngrok" ]; then
    echo "❌ 未找到ngrok，请先运行: ./setup_ngrok_simple.sh"
    exit 1
fi

if [ ! -f "app.py" ]; then
    echo "❌ 未找到app.py，请确保在ros2_wiki目录下运行"
    exit 1
fi

# 清理之前的进程
echo "🧹 清理之前的进程..."
pkill -f "python3 simple_server_test.py" || true
pkill -f "./ngrok" || true
sleep 2

# 创建日志文件
LOG_FILE="auto_restart.log"
echo "$(date): 启动自动重连脚本" > $LOG_FILE

# 重连计数器
RESTART_COUNT=0

# 信号处理函数
cleanup() {
    echo ""
    echo "🛑 收到停止信号，正在清理..."
    pkill -f "python3 simple_server_test.py" || true
    pkill -f "./ngrok" || true
    echo "$(date): 手动停止服务" >> $LOG_FILE
    echo "✅ 服务已停止"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 启动Flask应用
start_flask() {
    echo "🐍 启动Flask应用..."
    # 检查数据库
    if [ ! -f "simple_wiki.db" ]; then
        echo "📦 初始化数据库..."
        python3 init_sample_data.py
    fi
    
    # 启动Flask
    python3 simple_server_test.py &
    FLASK_PID=$!
    
    # 等待Flask启动
    sleep 3
    
    # 检查Flask是否成功启动
    if ! kill -0 $FLASK_PID 2>/dev/null; then
        echo "❌ Flask启动失败"
        echo "$(date): Flask启动失败" >> $LOG_FILE
        return 1
    fi
    
    echo "✅ Flask应用启动成功 (PID: $FLASK_PID)"
    return 0
}

# 启动ngrok
start_ngrok() {
    echo "🌐 启动ngrok隧道..."
    
    # 启动ngrok
    ./ngrok http 5000 --log=stdout > ngrok_auto.log 2>&1 &
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
        echo "❌ 获取公网地址失败"
        echo "$(date): ngrok启动失败" >> $LOG_FILE
        return 1
    fi
    
    echo "✅ ngrok隧道建立成功"
    echo "🌍 公网地址: $PUBLIC_URL"
    echo "$(date): 隧道建立成功 - $PUBLIC_URL" >> $LOG_FILE
    
    return 0
}

# 主循环
main_loop() {
    while true; do
        RESTART_COUNT=$((RESTART_COUNT + 1))
        
        echo ""
        echo "🚀 第 $RESTART_COUNT 次启动 ($(date))"
        echo "==============================="
        
        # 启动Flask
        if ! start_flask; then
            echo "⚠️ Flask启动失败，5秒后重试..."
            sleep 5
            continue
        fi
        
        # 启动ngrok
        if ! start_ngrok; then
            echo "⚠️ ngrok启动失败，5秒后重试..."
            pkill -f "python3 simple_server_test.py" || true
            sleep 5
            continue
        fi
        
        # 显示信息
        echo ""
        echo "🎉 服务运行中！"
        echo "==============="
        echo "📱 本地访问: http://localhost:5000"
        echo "🌍 公网访问: $PUBLIC_URL"
        echo "📊 ngrok面板: http://localhost:4040"
        echo ""
        echo "📋 默认账户："
        echo "   管理员: admin / admin123"
        echo "   用户: ros2_learner / user123"
        echo ""
        echo "💡 提示："
        echo "   - 免费版ngrok约8小时后自动重连"
        echo "   - 每次重连公网地址会变化"
        echo "   - 按Ctrl+C停止服务"
        echo ""
        
        # 监控ngrok进程
        while true; do
            if ! kill -0 $NGROK_PID 2>/dev/null; then
                echo "⚠️ ngrok进程已停止，准备重新启动..."
                echo "$(date): ngrok断连，准备重启" >> $LOG_FILE
                break
            fi
            
            if ! kill -0 $FLASK_PID 2>/dev/null; then
                echo "⚠️ Flask进程已停止，准备重新启动..."
                echo "$(date): Flask异常停止，准备重启" >> $LOG_FILE
                break
            fi
            
            sleep 30  # 每30秒检查一次
        done
        
        # 清理进程
        pkill -f "python3 simple_server_test.py" || true
        pkill -f "./ngrok" || true
        
        echo "🔄 5秒后重新启动..."
        sleep 5
    done
}

# 开始主循环
echo "🎬 开始自动重连循环..."
main_loop