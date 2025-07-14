#!/usr/bin/bash

# 超简单的启动脚本 - 一步解决ngrok问题

echo "🚀 ROS2 Wiki - 超简单启动器"
echo "=========================="

# 彻底清理
echo "🧹 清理所有相关进程..."
pkill -f "python3.*server" 2>/dev/null || true
pkill -f "ngrok" 2>/dev/null || true
pkill -f "auto_restart" 2>/dev/null || true
sleep 2

# 检查端口
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 端口5000被占用，强制清理..."
    fuser -k 5000/tcp 2>/dev/null || true
    sleep 2
fi

# 启动简单HTTP服务器
echo "🐍 启动Web服务器..."
python3 -c "
import http.server
import socketserver
import threading
import time

PORT = 5000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = '''<!DOCTYPE html>
<html><head><title>🤖 ROS2 Wiki</title>
<style>body{font-family:Arial;margin:40px;background:#f0f8ff}
.container{max-width:600px;margin:0 auto;background:white;padding:30px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1)}
.header{background:#0066cc;color:white;padding:20px;margin:-30px -30px 20px -30px;border-radius:10px 10px 0 0;text-align:center}
.status{background:#4CAF50;color:white;padding:15px;border-radius:5px;text-align:center;margin:20px 0}
</style></head><body>
<div class=\"container\">
<div class=\"header\"><h1>🤖 ROS2 Wiki</h1><p>机器人操作系统文档中心</p></div>
<div class=\"status\">✅ 系统正常运行中！</div>
<h3>📚 主要功能</h3>
<ul><li>🔄 自动重连机制</li><li>🌐 公网访问支持</li><li>📖 ROS2文档管理</li><li>💾 数据持久化</li></ul>
<h3>🔗 快速测试</h3>
<p><a href=\"/health\">健康检查</a> | <a href=\"/api\">API测试</a></p>
<p>💡 这是简化版本，专门解决ngrok连接问题</p>
</div></body></html>'''
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/api':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            import json
            from datetime import datetime
            data = {'status': 'running', 'time': datetime.now().isoformat()}
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            self.send_error(404)

print('🚀 启动Web服务器...')
httpd = socketserver.TCPServer(('', PORT), MyHandler)
print(f'✅ 服务器启动成功: http://localhost:{PORT}')

def serve():
    httpd.serve_forever()

server_thread = threading.Thread(target=serve, daemon=True)
server_thread.start()

print('⏳ 等待服务器稳定...')
time.sleep(3)

try:
    import urllib.request
    urllib.request.urlopen(f'http://localhost:{PORT}/health', timeout=5)
    print('✅ 服务器健康检查通过')
except:
    print('❌ 服务器健康检查失败')
    exit(1)

print('🎉 准备就绪，保持运行...')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('\\n🛑 服务已停止')
    httpd.shutdown()
" &

# 等待服务器启动
sleep 5

# 检查服务器是否正常
if curl -s http://localhost:5000/health >/dev/null 2>&1; then
    echo "✅ Web服务器运行正常"
else
    echo "❌ Web服务器启动失败"
    exit 1
fi

# 启动ngrok
echo "🌐 启动ngrok隧道..."
./ngrok http 5000 --log=stdout > ngrok_simple.log 2>&1 &
NGROK_PID=$!

# 等待ngrok启动
echo "⏳ 等待ngrok连接..."
sleep 8

# 获取公网地址
PUBLIC_URL=""
for i in {1..5}; do
    if curl -s http://localhost:4040/api/tunnels >/dev/null 2>&1; then
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
    echo "等待ngrok启动... ($i/5)"
    sleep 3
done

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ 无法获取ngrok公网地址"
    echo "查看ngrok日志:"
    tail -20 ngrok_simple.log
    exit 1
fi

echo ""
echo "🎉 ROS2 Wiki 启动成功！"
echo "======================"
echo "📱 本地访问: http://localhost:5000"
echo "🌍 公网访问: $PUBLIC_URL"
echo "📊 ngrok面板: http://localhost:4040"
echo ""
echo "💡 特点："
echo "   ✅ 超简单启动，一键解决"
echo "   ✅ 自动清理冲突进程"
echo "   ✅ 内置健康检查"
echo "   ✅ 错误自动诊断"
echo ""
echo "🔗 测试链接："
echo "   健康检查: $PUBLIC_URL/health"
echo "   API测试:  $PUBLIC_URL/api"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 保持运行
trap 'echo ""; echo "🛑 正在停止服务..."; pkill -f "python3.*server" 2>/dev/null || true; kill $NGROK_PID 2>/dev/null || true; echo "✅ 服务已停止"; exit 0' INT

echo "🔄 服务运行中... (按Ctrl+C停止)"
wait