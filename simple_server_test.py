#!/usr/bin/env python3
"""
最简单的HTTP服务器，用于测试ngrok
"""
import http.server
import socketserver
import os

PORT = 5000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>🤖 ROS2 Wiki</title>
                <meta charset="utf-8">
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 40px; 
                        background: #f5f5f5;
                    }
                    .container {
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    .header { 
                        background: #0066cc; 
                        color: white; 
                        padding: 20px; 
                        margin: -30px -30px 30px -30px;
                        border-radius: 10px 10px 0 0;
                    }
                    .status {
                        background: #4CAF50;
                        color: white;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }
                    .info-box {
                        background: #e3f2fd;
                        padding: 15px;
                        border-left: 4px solid #2196F3;
                        margin: 20px 0;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 ROS2 Wiki</h1>
                        <p>机器人操作系统文档中心</p>
                    </div>
                    
                    <div class="status">
                        ✅ ROS2 Wiki 正在通过 ngrok 运行！
                    </div>
                    
                    <div class="info-box">
                        <h3>📚 主要功能</h3>
                        <ul>
                            <li>🔄 ngrok 自动重连</li>
                            <li>🌐 公网访问支持</li>
                            <li>📖 ROS2 文档管理</li>
                            <li>💾 数据持久化</li>
                        </ul>
                    </div>
                    
                    <div class="info-box">
                        <h3>🔗 测试链接</h3>
                        <ul>
                            <li><a href="/health">健康检查</a></li>
                            <li><a href="/api/status">API状态</a></li>
                        </ul>
                    </div>
                    
                    <div class="info-box">
                        <h3>💡 使用说明</h3>
                        <p>这是一个简化版本，用于测试 ngrok 连接稳定性。</p>
                        <p>自动重连功能已启用，断连后会在5秒内自动恢复。</p>
                    </div>
                </div>
            </body>
            </html>
            '''
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            import json
            from datetime import datetime
            status = {
                "status": "running",
                "message": "ROS2 Wiki API 正常运行",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(status).encode('utf-8'))
            
        else:
            super().do_GET()

if __name__ == "__main__":
    print("🚀 启动ROS2 Wiki简化版服务器...")
    print(f"📱 本地访问: http://localhost:{PORT}")
    print("🔗 健康检查: http://localhost:{}/health".format(PORT))
    print("💚 API状态: http://localhost:{}/api/status".format(PORT))
    print("按 Ctrl+C 停止服务")
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"✅ 服务器启动成功，监听端口 {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")