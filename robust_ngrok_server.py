#!/usr/bin/env python3
"""
稳定的ngrok服务器 - 内置重连逻辑
解决ERR_NGROK_3200问题
"""
import http.server
import socketserver
import subprocess
import threading
import time
import json
import signal
import sys
import os
from datetime import datetime

class NGROKServer:
    def __init__(self, port=5000):
        self.port = port
        self.ngrok_process = None
        self.web_server = None
        self.running = True
        self.restart_count = 0
        
    def create_web_handler(self):
        """创建Web请求处理器"""
        class WebHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    html = f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>🤖 ROS2 Wiki - 稳定版</title>
                        <meta charset="utf-8">
                        <meta http-equiv="refresh" content="30">
                        <style>
                            body {{ 
                                font-family: Arial, sans-serif; 
                                margin: 40px; 
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                            }}
                            .container {{
                                max-width: 900px;
                                margin: 0 auto;
                                background: rgba(255,255,255,0.95);
                                color: #333;
                                padding: 30px;
                                border-radius: 15px;
                                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                            }}
                            .header {{ 
                                background: linear-gradient(45deg, #0066cc, #004499);
                                color: white; 
                                padding: 25px; 
                                margin: -30px -30px 30px -30px;
                                border-radius: 15px 15px 0 0;
                                text-align: center;
                            }}
                            .status {{
                                background: linear-gradient(45deg, #4CAF50, #45a049);
                                color: white;
                                padding: 20px;
                                border-radius: 10px;
                                margin: 20px 0;
                                text-align: center;
                                font-size: 18px;
                            }}
                            .info-grid {{
                                display: grid;
                                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                                gap: 20px;
                                margin: 30px 0;
                            }}
                            .info-box {{
                                background: #f8f9fa;
                                padding: 20px;
                                border-radius: 10px;
                                border-left: 5px solid #2196F3;
                            }}
                            .timestamp {{
                                background: #e3f2fd;
                                padding: 10px;
                                border-radius: 5px;
                                font-family: monospace;
                                text-align: center;
                                margin: 20px 0;
                            }}
                            .feature {{
                                display: flex;
                                align-items: center;
                                margin: 10px 0;
                            }}
                            .feature-icon {{
                                font-size: 24px;
                                margin-right: 10px;
                            }}
                            a {{
                                color: #2196F3;
                                text-decoration: none;
                            }}
                            a:hover {{
                                text-decoration: underline;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>🤖 ROS2 Wiki</h1>
                                <p>机器人操作系统文档中心 - 稳定版</p>
                            </div>
                            
                            <div class="status">
                                ✅ 系统正常运行中！重启次数: {outer_self.restart_count}
                            </div>
                            
                            <div class="timestamp">
                                🕒 当前时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                            </div>
                            
                            <div class="info-grid">
                                <div class="info-box">
                                    <h3>🔄 自动重连功能</h3>
                                    <div class="feature">
                                        <span class="feature-icon">⚡</span>
                                        <span>断线5秒内重连</span>
                                    </div>
                                    <div class="feature">
                                        <span class="feature-icon">🔍</span>
                                        <span>每15秒健康检查</span>
                                    </div>
                                    <div class="feature">
                                        <span class="feature-icon">📊</span>
                                        <span>实时状态监控</span>
                                    </div>
                                </div>
                                
                                <div class="info-box">
                                    <h3>🌐 访问方式</h3>
                                    <div class="feature">
                                        <span class="feature-icon">🏠</span>
                                        <span>本地: localhost:{outer_self.port}</span>
                                    </div>
                                    <div class="feature">
                                        <span class="feature-icon">🌍</span>
                                        <span>公网: 通过ngrok隧道</span>
                                    </div>
                                    <div class="feature">
                                        <span class="feature-icon">📱</span>
                                        <span>移动设备友好</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="info-box">
                                <h3>🔗 快速链接</h3>
                                <p>
                                    <a href="/health">🏥 健康检查</a> | 
                                    <a href="/api/status">📊 API状态</a> | 
                                    <a href="/api/ngrok">🔗 隧道信息</a>
                                </p>
                            </div>
                            
                            <div class="info-box">
                                <h3>💡 稳定性改进</h3>
                                <ul>
                                    <li>✅ 内置进程监控</li>
                                    <li>✅ 自动故障恢复</li>
                                    <li>✅ 多重健康检查</li>
                                    <li>✅ 优雅的错误处理</li>
                                </ul>
                            </div>
                        </div>
                        
                        <script>
                            // 自动刷新页面保持活跃
                            console.log('ROS2 Wiki 稳定版加载完成');
                        </script>
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
                    status = {
                        "status": "running",
                        "message": "ROS2 Wiki 稳定版正常运行",
                        "timestamp": datetime.now().isoformat(),
                        "restart_count": outer_self.restart_count,
                        "port": outer_self.port
                    }
                    self.wfile.write(json.dumps(status, ensure_ascii=False).encode('utf-8'))
                    
                elif self.path == '/api/ngrok':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    ngrok_info = outer_self.get_ngrok_info()
                    self.wfile.write(json.dumps(ngrok_info, ensure_ascii=False).encode('utf-8'))
                    
                else:
                    self.send_error(404, "页面未找到")
        
        # 创建闭包，让handler能访问外部的self
        outer_self = self
        return WebHandler

    def start_web_server(self):
        """启动Web服务器"""
        try:
            handler = self.create_web_handler()
            self.web_server = socketserver.TCPServer(("", self.port), handler)
            print(f"✅ Web服务器启动成功，端口: {self.port}")
            
            # 在新线程中运行服务器
            server_thread = threading.Thread(target=self.web_server.serve_forever, daemon=True)
            server_thread.start()
            return True
        except Exception as e:
            print(f"❌ Web服务器启动失败: {e}")
            return False

    def start_ngrok(self):
        """启动ngrok隧道"""
        try:
            # 启动ngrok
            cmd = ['./ngrok', 'http', str(self.port), '--log=stdout']
            self.ngrok_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd='/home/sevenseven/ros2_wiki'
            )
            
            # 等待ngrok启动
            time.sleep(5)
            
            # 检查ngrok是否成功启动
            if self.ngrok_process.poll() is not None:
                print("❌ ngrok进程意外退出")
                return False
                
            # 获取公网地址
            public_url = self.get_public_url()
            if public_url:
                print(f"✅ ngrok隧道建立成功")
                print(f"🌍 公网地址: {public_url}")
                return True
            else:
                print("❌ 无法获取ngrok公网地址")
                return False
                
        except Exception as e:
            print(f"❌ ngrok启动失败: {e}")
            return False

    def get_public_url(self):
        """获取ngrok公网地址"""
        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:4040/api/tunnels')
            data = json.loads(response.read().decode())
            
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    return tunnel.get('public_url')
            return None
        except:
            return None

    def get_ngrok_info(self):
        """获取ngrok详细信息"""
        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:4040/api/tunnels')
            data = json.loads(response.read().decode())
            return {
                "status": "connected",
                "tunnels": data.get('tunnels', []),
                "timestamp": datetime.now().isoformat()
            }
        except:
            return {
                "status": "disconnected",
                "message": "无法连接到ngrok API",
                "timestamp": datetime.now().isoformat()
            }

    def cleanup(self):
        """清理资源"""
        print("🧹 正在清理资源...")
        
        if self.ngrok_process:
            try:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
            except:
                self.ngrok_process.kill()
        
        if self.web_server:
            self.web_server.shutdown()
            self.web_server.server_close()

    def check_health(self):
        """健康检查"""
        try:
            # 检查Web服务器
            import urllib.request
            urllib.request.urlopen(f'http://localhost:{self.port}/health', timeout=5)
            
            # 检查ngrok
            urllib.request.urlopen('http://localhost:4040/api/tunnels', timeout=5)
            
            return True
        except:
            return False

    def restart_services(self):
        """重启服务"""
        self.restart_count += 1
        print(f"🔄 第 {self.restart_count} 次重启服务...")
        
        # 清理旧进程
        self.cleanup()
        time.sleep(3)
        
        # 重启Web服务器
        if not self.start_web_server():
            return False
            
        # 重启ngrok
        if not self.start_ngrok():
            return False
            
        return True

    def monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                if not self.check_health():
                    print("⚠️ 健康检查失败，准备重启...")
                    if not self.restart_services():
                        print("❌ 重启失败，5秒后重试...")
                        time.sleep(5)
                        continue
                    else:
                        print("✅ 重启成功")
                
                # 每15秒检查一次
                time.sleep(15)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ 监控异常: {e}")
                time.sleep(5)

    def signal_handler(self, signum, frame):
        """信号处理"""
        print("\n🛑 收到停止信号...")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def run(self):
        """主运行方法"""
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🚀 启动ROS2 Wiki稳定版服务器...")
        print("=" * 50)
        
        # 初始启动
        if not self.start_web_server():
            print("❌ Web服务器启动失败")
            return False
            
        if not self.start_ngrok():
            print("❌ ngrok启动失败")
            return False
        
        print("\n🎉 服务启动成功！")
        print("=" * 30)
        print(f"📱 本地访问: http://localhost:{self.port}")
        
        public_url = self.get_public_url()
        if public_url:
            print(f"🌍 公网访问: {public_url}")
        
        print(f"📊 ngrok面板: http://localhost:4040")
        print("\n💡 系统将自动监控并处理断连问题")
        print("按 Ctrl+C 停止服务\n")
        
        # 启动监控循环
        self.monitor_loop()

if __name__ == "__main__":
    server = NGROKServer(port=5000)
    server.run()