#!/usr/bin/env python3
"""
ROS2 Wiki - Flask应用入口文件
专门为Render部署优化
"""

import os
import sys
from flask import Flask

# 创建Flask应用实例 - Gunicorn需要这个名字
app = Flask(__name__)

# 基本配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'render-deployment-key')

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ROS2 Wiki</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .success { color: #28a745; }
            .info { color: #007bff; }
        </style>
    </head>
    <body>
        <h1 class="success">🎉 ROS2 Wiki 部署成功!</h1>
        <p class="info">应用正在Render平台上运行</p>
        <ul>
            <li><a href="/health">健康检查</a></li>
            <li><a href="/debug">调试信息</a></li>
        </ul>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """健康检查端点"""
    return {
        'status': 'ok', 
        'message': '应用运行正常',
        'platform': 'Render',
        'python_version': sys.version
    }

@app.route('/debug')
def debug():
    """调试信息页面"""
    env_vars = [
        'FLASK_ENV', 'SECRET_KEY', 'DATABASE_URL', 
        'ADMIN_USERNAME', 'ADMIN_PASSWORD', 'PORT'
    ]
    
    env_info = []
    for var in env_vars:
        value = os.environ.get(var, 'NOT_SET')
        # 隐藏敏感信息
        if any(word in var for word in ['PASSWORD', 'SECRET', 'KEY']):
            value = f'[SET - {len(value)} chars]' if value != 'NOT_SET' else 'NOT_SET'
        env_info.append(f"{var}: {value}")
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ROS2 Wiki - 调试信息</title>
        <style>
            body {{ font-family: monospace; margin: 20px; }}
            .debug-info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h2>🔧 调试信息</h2>
        <div class="debug-info">
            <p><strong>Python版本:</strong> {sys.version}</p>
            <p><strong>当前目录:</strong> {os.getcwd()}</p>
            <p><strong>Flask应用:</strong> {app}</p>
            <h3>环境变量:</h3>
            <ul>
                {"".join(f"<li>{info}</li>" for info in env_info)}
            </ul>
        </div>
        <p><a href="/">返回首页</a></p>
    </body>
    </html>
    '''

# 用于本地开发的启动函数
def main():
    """本地开发服务器"""
    print("=== ROS2 Wiki 本地开发服务器 ===")
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动地址: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()