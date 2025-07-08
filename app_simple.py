#!/usr/bin/env python3
"""
ROS2 Wiki 简化版应用
用于测试ngrok连接
"""
import sys
import os

# 添加本地库路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
    print("✅ 使用本地简化版Flask")
except ImportError:
    print("❌ Flask导入失败")
    sys.exit(1)

import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['DATABASE'] = 'simple_wiki.db'

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # 创建简单的文档表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入示例数据
    cursor.execute('SELECT COUNT(*) FROM documents')
    if cursor.fetchone()[0] == 0:
        sample_docs = [
            ("ROS2 入门指南", "# ROS2 入门指南\n\n欢迎来到ROS2世界！这是一个机器人操作系统。"),
            ("安装教程", "# ROS2 安装教程\n\n1. 更新系统\n2. 安装ROS2\n3. 设置环境变量"),
            ("基础概念", "# ROS2 基础概念\n\n- 节点(Node)\n- 主题(Topic)\n- 服务(Service)\n- 参数(Parameter)")
        ]
        
        for title, content in sample_docs:
            cursor.execute('INSERT INTO documents (title, content) VALUES (?, ?)', (title, content))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """首页"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents ORDER BY created_at DESC')
    documents = cursor.fetchall()
    conn.close()
    
    # 简化版模板渲染
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ROS2 Wiki</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { background: #0066cc; color: white; padding: 20px; margin-bottom: 20px; }
            .doc-item { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
            .doc-title { font-size: 18px; font-weight: bold; color: #0066cc; }
            .doc-content { margin-top: 10px; color: #666; }
            .footer { margin-top: 40px; text-align: center; color: #666; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 ROS2 Wiki</h1>
            <p>机器人操作系统文档中心</p>
        </div>
        
        <h2>📚 文档列表</h2>
    '''
    
    for doc in documents:
        html += f'''
        <div class="doc-item">
            <div class="doc-title">{doc[1]}</div>
            <div class="doc-content">{doc[2][:100]}...</div>
            <small>创建时间: {doc[3]}</small>
        </div>
        '''
    
    html += '''
        <div class="footer">
            <p>🎉 ROS2 Wiki 通过 ngrok 自动重连正在运行！</p>
            <p>💡 这是一个简化版本，用于测试 ngrok 连接稳定性</p>
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/api/status')
def api_status():
    """API状态检查"""
    return jsonify({
        "status": "running",
        "message": "ROS2 Wiki API 正常运行",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """健康检查"""
    return "OK"

if __name__ == '__main__':
    print("🚀 启动ROS2 Wiki简化版...")
    
    # 初始化数据库
    if not os.path.exists(app.config['DATABASE']):
        print("📦 初始化数据库...")
        init_db()
    
    print("✅ 数据库就绪")
    print("🌍 启动Web服务器...")
    print("📱 本地访问: http://localhost:5000")
    print("🔗 API状态: http://localhost:5000/api/status")
    print("💚 健康检查: http://localhost:5000/health")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)