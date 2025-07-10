#!/usr/bin/env python3
"""
ROS2 Wiki - 轻量级Flask应用
使用尽可能少的依赖，主要依赖Python标准库
"""

import os
import sys
import sqlite3
import hashlib
import re
import json
import base64
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse, parse_qs
import http.server
import socketserver
from http.cookies import SimpleCookie

# 简化的Flask应用模拟
class SimpleApp:
    def __init__(self):
        self.routes = {}
        self.before_request_funcs = []
        self.config = {
            'SECRET_KEY': 'ros2-wiki-secret-key-2024',
            'DATABASE': 'ros2_wiki.db'
        }
        
    def route(self, path, methods=['GET']):
        def decorator(func):
            for method in methods:
                key = f"{method}:{path}"
                self.routes[key] = func
            return func
        return decorator
    
    def before_request(self, func):
        self.before_request_funcs.append(func)
        return func

app = SimpleApp()

# 全局变量存储会话信息
sessions = {}

# 数据库函数
def get_db_connection():
    """获取SQLite数据库连接"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """初始化数据库表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 文档表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER,
            category TEXT DEFAULT 'ROS2基础',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # 评论表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            user_id INTEGER,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# 用户管理
class User:
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin
    
    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['email'], user_data['is_admin'])
        return None
    
    @staticmethod
    def authenticate(username, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            return User(user_data['id'], user_data['username'], user_data['email'], user_data['is_admin'])
        return None

# 简化的密码哈希函数
def generate_password_hash(password):
    return hashlib.sha256((password + 'salt').encode()).hexdigest()

def check_password_hash(hash_value, password):
    return hash_value == generate_password_hash(password)

# 简化的Markdown渲染
def render_markdown(content):
    # 基础Markdown渲染
    html = content
    
    # 标题
    html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # 代码块
    html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    
    # 行内代码
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # 粗体
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # 段落
    paragraphs = html.split('\n\n')
    html = '</p><p>'.join(paragraphs)
    html = f'<p>{html}</p>'
    
    # 清理空段落
    html = re.sub(r'<p></p>', '', html)
    
    return html

# HTTP请求处理器
class WikiHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # 禁用日志输出
        pass
    
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def handle_request(self):
        try:
            # 解析路径
            path = self.path.split('?')[0]
            method = self.command
            
            # 获取查询参数
            query_string = self.path.split('?')[1] if '?' in self.path else ''
            query_params = parse_qs(query_string)
            
            # 获取POST数据
            post_data = {}
            if method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    post_data = parse_qs(body)
                    # 转换为单值字典
                    post_data = {k: v[0] if len(v) == 1 else v for k, v in post_data.items()}
            
            # 处理会话
            session_id = self.get_session_id()
            current_user = self.get_current_user(session_id)
            
            # 路由匹配
            route_key = f"{method}:{path}"
            if route_key in app.routes:
                response = app.routes[route_key](query_params, post_data, current_user)
                self.send_response_data(response)
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_error(500, str(e))
    
    def get_session_id(self):
        """获取会话ID"""
        cookie_header = self.headers.get('Cookie', '')
        if 'session_id=' in cookie_header:
            return cookie_header.split('session_id=')[1].split(';')[0]
        return None
    
    def get_current_user(self, session_id):
        """获取当前用户"""
        if session_id and session_id in sessions:
            user_id = sessions[session_id].get('user_id')
            if user_id:
                return User.get(user_id)
        return None
    
    def send_response_data(self, response):
        """发送响应数据"""
        if isinstance(response, dict):
            # JSON响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        elif isinstance(response, tuple):
            # 重定向响应
            status, location = response
            self.send_response(status)
            self.send_header('Location', location)
            self.end_headers()
        else:
            # HTML响应
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))

# 路由定义
@app.route('/')
def index(query_params, post_data, current_user):
    """首页"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, u.username 
        FROM documents d 
        LEFT JOIN users u ON d.author_id = u.id 
        ORDER BY d.created_at DESC
        LIMIT 10
    ''')
    documents = cursor.fetchall()
    conn.close()
    
    # 生成HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ROS2 Wiki - 首页</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-robot"></i> ROS2 Wiki</a>
            <div class="navbar-nav ms-auto">
                {get_nav_html(current_user)}
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8">
                <h1>ROS2 技术教程</h1>
                <p class="lead">学习ROS2机器人操作系统，掌握现代机器人开发技术</p>
                
                <div class="row">
'''
    
    for doc in documents:
        html += f'''
                    <div class="col-md-6 mb-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">{doc['title']}</h5>
                                <p class="card-text">
                                    <small class="text-muted">
                                        分类：{doc['category']} | 
                                        作者：{doc['username'] or '管理员'} | 
                                        发布时间：{doc['created_at'][:16]}
                                    </small>
                                </p>
                                <a href="/document/{doc['id']}" class="btn btn-primary">阅读教程</a>
                            </div>
                        </div>
                    </div>
'''
    
    if not documents:
        html += '''
                    <div class="alert alert-info">
                        <h4>欢迎来到ROS2 Wiki！</h4>
                        <p>请管理员添加教程内容。</p>
                    </div>
'''
    
    html += '''
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>ROS2学习路径</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item">🚀 ROS2环境搭建</li>
                            <li class="list-group-item">📦 包管理和工作空间</li>
                            <li class="list-group-item">🔄 节点通信机制</li>
                            <li class="list-group-item">🛠️ 常用工具和调试</li>
                            <li class="list-group-item">🤖 机器人应用开发</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    return html

@app.route('/login', methods=['GET', 'POST'])
def login(query_params, post_data, current_user):
    """用户登录"""
    if post_data:  # POST请求
        username = post_data.get('username', '')
        password = post_data.get('password', '')
        
        user = User.authenticate(username, password)
        if user:
            # 创建会话
            import uuid
            session_id = str(uuid.uuid4())
            sessions[session_id] = {'user_id': user.id, 'username': user.username}
            
            # 返回重定向
            return (302, '/')
        else:
            return render_login_page("用户名或密码错误")
    else:  # GET请求
        return render_login_page()

def render_login_page(error_msg=""):
    """渲染登录页面"""
    error_html = f'<div class="alert alert-danger">{error_msg}</div>' if error_msg else ''
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - ROS2 Wiki</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        <div class="row justify-content-center mt-5">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h4>用户登录</h4>
                    </div>
                    <div class="card-body">
                        {error_html}
                        <form method="POST">
                            <div class="mb-3">
                                <label for="username" class="form-label">用户名</label>
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">密码</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary">登录</button>
                            <a href="/register" class="btn btn-outline-secondary">注册新账户</a>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/health')
def health(query_params, post_data, current_user):
    """健康检查"""
    return {
        'status': 'ok',
        'message': 'ROS2 Wiki 运行正常',
        'features': {
            'database': 'SQLite',
            'user_management': True,
            'document_system': True,
            'search': True,
            'cms': True,
            'comments': True
        }
    }

def get_nav_html(current_user):
    """生成导航HTML"""
    if current_user:
        admin_link = '<a class="nav-link" href="/admin">管理后台</a>' if current_user.is_admin else ''
        return f'''
            <span class="navbar-text me-3">欢迎，{current_user.username}！</span>
            {admin_link}
            <a class="nav-link" href="/logout">退出</a>
        '''
    else:
        return '''
            <a class="nav-link" href="/login">登录</a>
            <a class="nav-link" href="/register">注册</a>
        '''

def init_sample_data():
    """初始化示例数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        # 创建默认管理员
        admin_hash = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                      ('admin', 'admin@ros2wiki.com', admin_hash, 1))
        
        # 添加示例用户
        cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                      ('ros2_user', 'user@ros2wiki.com', generate_password_hash('user123'), 0))
        
        # 添加示例文档
        sample_content = '''# ROS2快速入门指南

欢迎来到ROS2世界！本指南将帮助您快速上手ROS2机器人操作系统。

## 什么是ROS2？

ROS2（Robot Operating System 2）是下一代机器人操作系统，提供了：

- **分布式架构**：支持多机器人协作
- **实时通信**：DDS中间件保证低延迟
- **跨平台支持**：Linux、Windows、macOS
- **安全特性**：身份验证和加密通信

## 安装ROS2

```bash
# Ubuntu 22.04
sudo apt update && sudo apt install ros-humble-desktop

# 环境配置
source /opt/ros/humble/setup.bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

## 创建第一个工作空间

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
source install/setup.bash
```

开始您的ROS2学习之旅！'''
        
        cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (?, ?, ?, ?)',
                      ('ROS2快速入门指南', sample_content, 1, 'ROS2基础'))
        
        conn.commit()
        print("✅ 示例数据初始化完成")
    
    conn.close()

def main():
    """启动服务器"""
    try:
        init_database()
        init_sample_data()
        print("✅ ROS2 Wiki 轻量级版本初始化完成")
    except Exception as e:
        print(f"❌ 初始化错误: {e}")
        return
    
    PORT = int(os.environ.get('PORT', 5000))
    
    print("=== ROS2 Wiki 轻量级版本 ===")
    print(f"🚀 启动地址: http://localhost:{PORT}")
    print(f"👤 默认管理员: admin / admin123")
    print(f"👤 测试用户: ros2_user / user123")
    print(f"💡 轻量级实现 - 最小依赖")
    
    with socketserver.TCPServer(("", PORT), WikiHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ 服务器已停止")

if __name__ == '__main__':
    main()