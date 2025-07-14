#!/usr/bin/env python3
"""
超简化版ROS2 Wiki服务器
只使用Python标准库，无需安装任何依赖
"""
import http.server
import socketserver
import json
import urllib.parse
import sqlite3
import hashlib
import os
from datetime import datetime

# 数据库初始化
def init_db():
    conn = sqlite3.connect('simple_wiki.db')
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 文档表
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
            ('ROS2快速入门', '''# ROS2快速入门指南

## 什么是ROS2？
ROS2是下一代机器人操作系统...

## 安装ROS2
```bash
sudo apt update
sudo apt install ros-humble-desktop
```

## 第一个节点
```python
import rclpy
from rclpy.node import Node

class HelloWorld(Node):
    def __init__(self):
        super().__init__('hello_world')
        self.get_logger().info('Hello ROS2!')

def main():
    rclpy.init()
    node = HelloWorld()
    rclpy.spin(node)
    rclpy.shutdown()
```
'''),
            ('ROS2话题通信', '''# ROS2话题通信

## 发布者
```python
import rclpy
from std_msgs.msg import String

class Publisher(Node):
    def __init__(self):
        super().__init__('publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        self.timer = self.create_timer(0.5, self.timer_callback)

    def timer_callback(self):
        msg = String()
        msg.data = 'Hello World'
        self.publisher_.publish(msg)
```

## 订阅者
```python
class Subscriber(Node):
    def __init__(self):
        super().__init__('subscriber')
        self.subscription = self.create_subscription(
            String, 'topic', self.callback, 10)

    def callback(self, msg):
        self.get_logger().info(f'Received: {msg.data}')
```
''')
        ]
        
        for title, content in sample_docs:
            cursor.execute('INSERT INTO documents (title, content) VALUES (?, ?)', 
                          (title, content))
    
    conn.commit()
    conn.close()

class WikiHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 获取文档列表
            conn = sqlite3.connect('simple_wiki.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, created_at FROM documents ORDER BY id')
            docs = cursor.fetchall()
            conn.close()
            
            html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ROS2 Wiki</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
        .doc-card {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .doc-card:hover {{ background: #f5f5f5; }}
        .doc-link {{ text-decoration: none; color: #2c3e50; }}
        .doc-title {{ font-size: 18px; font-weight: bold; }}
        .doc-date {{ color: #666; font-size: 14px; }}
        .access-info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 ROS2 Wiki</h1>
        <p>机器人操作系统学习平台</p>
    </div>
    
    <div class="access-info">
        <h3>🌍 公网访问已启动！</h3>
        <p>您的网站现在可以通过ngrok访问。启动命令：<code>./ngrok http 8000</code></p>
    </div>
    
    <h2>📚 教程列表</h2>
'''
            
            for doc_id, title, created_at in docs:
                html += f'''
    <div class="doc-card">
        <a href="/doc/{doc_id}" class="doc-link">
            <div class="doc-title">{title}</div>
            <div class="doc-date">发布时间: {created_at[:16]}</div>
        </a>
    </div>'''
            
            html += '''
</body>
</html>'''
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path.startswith('/doc/'):
            doc_id = self.path.split('/')[-1]
            try:
                doc_id = int(doc_id)
                conn = sqlite3.connect('simple_wiki.db')
                cursor = conn.cursor()
                cursor.execute('SELECT title, content FROM documents WHERE id = ?', (doc_id,))
                doc = cursor.fetchone()
                conn.close()
                
                if doc:
                    title, content = doc
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    # 简单的Markdown转HTML
                    html_content = content.replace('\n\n', '</p><p>')
                    html_content = html_content.replace('\n', '<br>')
                    html_content = f'<p>{html_content}</p>'
                    
                    # 代码块处理
                    import re
                    html_content = re.sub(
                        r'```(\w+)?\n(.*?)```',
                        r'<pre><code>\2</code></pre>',
                        html_content,
                        flags=re.DOTALL
                    )
                    
                    # 标题处理
                    html_content = re.sub(r'<p># (.*?)</p>', r'<h1>\1</h1>', html_content)
                    html_content = re.sub(r'<p>## (.*?)</p>', r'<h2>\1</h2>', html_content)
                    html_content = re.sub(r'<p>### (.*?)</p>', r'<h3>\1</h3>', html_content)
                    
                    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - ROS2 Wiki</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
        .back-link {{ color: #3498db; text-decoration: none; }}
        .back-link:hover {{ text-decoration: underline; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="back-link">← 返回首页</a>
        <h1>{title}</h1>
    </div>
    
    <div class="content">
        {html_content}
    </div>
</body>
</html>'''
                    
                    self.wfile.write(html.encode('utf-8'))
                else:
                    self.send_error(404, '文档不存在')
            except ValueError:
                self.send_error(400, '无效的文档ID')
        else:
            self.send_error(404, 'Page Not Found')

def main():
    init_db()
    PORT = 8000
    
    with socketserver.TCPServer(("", PORT), WikiHandler) as httpd:
        print(f"🚀 ROS2 Wiki 服务器启动成功！")
        print(f"📱 本地访问: http://localhost:{PORT}")
        print(f"🌍 公网访问: 启动 './ngrok http {PORT}' 获取公网地址")
        print(f"⚡ 超轻量版本 - 无需安装任何依赖包")
        print(f"🛑 按 Ctrl+C 停止服务")
        print("-" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ 服务器已停止")

if __name__ == "__main__":
    main()