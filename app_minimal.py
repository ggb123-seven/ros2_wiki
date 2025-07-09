#!/usr/bin/env python3
"""
最小化Flask应用 - 用于诊断Render部署问题
"""

import os
import sys
from flask import Flask

# 创建Flask应用实例（Gunicorn需要这个变量名）
app = Flask(__name__)

# 基本配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-key')

@app.route('/')
def home():
    return '''
    <h1>🎉 ROS2 Wiki 部署成功!</h1>
    <p>最小化版本正在运行</p>
    <p>下一步: 启用完整功能</p>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'message': '应用运行正常'}

@app.route('/debug')
def debug():
    """调试信息页面"""
    env_info = []
    env_vars = [
        'FLASK_ENV', 'SECRET_KEY', 'DATABASE_URL', 
        'ADMIN_USERNAME', 'ADMIN_PASSWORD', 'PORT'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NOT_SET')
        # 隐藏敏感信息
        if 'PASSWORD' in var or 'SECRET' in var:
            value = '*****' if value != 'NOT_SET' else 'NOT_SET'
        env_info.append(f"{var}: {value}")
    
    return f'''
    <h2>🔧 调试信息</h2>
    <p><strong>Python版本:</strong> {sys.version}</p>
    <p><strong>当前目录:</strong> {os.getcwd()}</p>
    <h3>环境变量:</h3>
    <ul>
        {"".join(f"<li>{info}</li>" for info in env_info)}
    </ul>
    '''

def main():
    """用于本地运行的函数"""
    print("=== ROS2 Wiki 最小化版本 ===")
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动服务器 - 端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()