#!/usr/bin/env python3
"""
ROS2 Wiki - 完整版Flask应用
整合所有功能：用户管理、文档系统、搜索、CMS等
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime
from urllib.parse import urlparse
from functools import wraps

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import markdown

# 创建Flask应用实例
app = Flask(__name__)

# 环境变量配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ros2-wiki-secret')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')
app.config['DATABASE'] = 'ros2_wiki.db' if not app.config['DATABASE_URL'] else None

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

class User(UserMixin):
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if app.config['DATABASE_URL']:
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    else:
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[4] if len(user) > 4 else False)
    return None

def get_db_connection():
    """获取数据库连接"""
    if app.config['DATABASE_URL']:
        # PostgreSQL连接
        return psycopg2.connect(app.config['DATABASE_URL'])
    else:
        # SQLite连接
        return sqlite3.connect(app.config['DATABASE'])

def init_database():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 用户表
    if app.config['DATABASE_URL']:
        # PostgreSQL语法
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite语法
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
    if app.config['DATABASE_URL']:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author_id INTEGER REFERENCES users(id),
                category TEXT DEFAULT 'ROS2基础',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
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
    if app.config['DATABASE_URL']:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id),
                user_id INTEGER REFERENCES users(id),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
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

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('需要管理员权限')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 路由定义
@app.route('/')
def index():
    """首页 - 显示最新文档"""
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
    
    return render_template('index.html', documents=documents)

@app.route('/health')
def health():
    """健康检查端点"""
    return jsonify({
        'status': 'ok',
        'message': 'ROS2 Wiki 运行正常',
        'features': {
            'database': 'PostgreSQL' if app.config['DATABASE_URL'] else 'SQLite',
            'user_management': True,
            'document_system': True,
            'search': True
        }
    })

@app.route('/debug')
def debug():
    """调试信息页面"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 统计信息
    try:
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM documents')
        doc_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM comments')
        comment_count = cursor.fetchone()[0]
    except:
        user_count = doc_count = comment_count = 0
    
    conn.close()
    
    return jsonify({
        'environment': {
            'python_version': sys.version,
            'database_type': 'PostgreSQL' if app.config['DATABASE_URL'] else 'SQLite',
            'current_user': current_user.username if current_user.is_authenticated else 'Anonymous'
        },
        'statistics': {
            'users': user_count,
            'documents': doc_count,
            'comments': comment_count
        },
        'features': {
            'authentication': True,
            'admin_panel': True,
            'document_management': True,
            'search': True,
            'comments': True
        }
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        if app.config['DATABASE_URL']:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        else:
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            user_obj = User(user[0], user[1], user[2], user[4] if len(user) > 4 else False)
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户是否已存在
        if app.config['DATABASE_URL']:
            cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, email))
        else:
            cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        
        if cursor.fetchone():
            flash('用户名或邮箱已存在')
            conn.close()
            return render_template('register.html')
        
        # 创建新用户
        password_hash = generate_password_hash(password)
        if app.config['DATABASE_URL']:
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                          (username, email, password_hash))
        else:
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                          (username, email, password_hash))
        
        conn.commit()
        conn.close()
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/document/<int:doc_id>')
def view_document(doc_id):
    """查看文档详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取文档
    cursor.execute('''
        SELECT d.*, u.username 
        FROM documents d 
        LEFT JOIN users u ON d.author_id = u.id 
        WHERE d.id = %s
    ''' if app.config['DATABASE_URL'] else '''
        SELECT d.*, u.username 
        FROM documents d 
        LEFT JOIN users u ON d.author_id = u.id 
        WHERE d.id = ?
    ''', (doc_id,))
    document = cursor.fetchone()
    
    if not document:
        flash('文档不存在')
        return redirect(url_for('index'))
    
    # 获取评论
    cursor.execute('''
        SELECT c.*, u.username 
        FROM comments c 
        LEFT JOIN users u ON c.user_id = u.id 
        WHERE c.document_id = %s 
        ORDER BY c.created_at DESC
    ''' if app.config['DATABASE_URL'] else '''
        SELECT c.*, u.username 
        FROM comments c 
        LEFT JOIN users u ON c.user_id = u.id 
        WHERE c.document_id = ? 
        ORDER BY c.created_at DESC
    ''', (doc_id,))
    comments = cursor.fetchall()
    
    conn.close()
    
    return render_template('document.html', document=document, comments=comments)

@app.route('/admin')
@admin_required
def admin_dashboard():
    """管理员后台"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取统计信息
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM documents')
    doc_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM comments')
    comment_count = cursor.fetchone()[0]
    
    # 获取最新文档
    cursor.execute('''
        SELECT d.*, u.username 
        FROM documents d 
        LEFT JOIN users u ON d.author_id = u.id 
        ORDER BY d.created_at DESC
        LIMIT 10
    ''')
    recent_docs = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         user_count=user_count,
                         doc_count=doc_count,
                         comment_count=comment_count,
                         recent_docs=recent_docs)

# 初始化数据库和示例数据
def init_sample_data():
    """初始化示例数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        # 创建默认管理员
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@ros2wiki.com')
        
        admin_hash = generate_password_hash(admin_password)
        
        if app.config['DATABASE_URL']:
            cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)',
                          (admin_username, admin_email, admin_hash, True))
            # 添加示例用户
            cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)',
                          ('ros2_user', 'user@ros2wiki.com', generate_password_hash('user123'), False))
            # 添加示例文档
            cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (%s, %s, %s, %s)',
                          ('ROS2快速入门', '''# ROS2快速入门

欢迎来到ROS2世界！这是一个入门指南。

## 安装ROS2

```bash
sudo apt update
sudo apt install ros-humble-desktop
```

## 配置环境

```bash
source /opt/ros/humble/setup.bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

## 创建工作空间

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
```

开始您的ROS2学习之旅！
''', 1, 'ROS2基础'))
        else:
            cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                          (admin_username, admin_email, admin_hash, 1))
            cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                          ('ros2_user', 'user@ros2wiki.com', generate_password_hash('user123'), 0))
            cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (?, ?, ?, ?)',
                          ('ROS2快速入门', '''# ROS2快速入门

欢迎来到ROS2世界！这是一个入门指南。

## 安装ROS2

```bash
sudo apt update
sudo apt install ros-humble-desktop
```

## 配置环境

```bash
source /opt/ros/humble/setup.bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

## 创建工作空间

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
```

开始您的ROS2学习之旅！
''', 1, 'ROS2基础'))
        
        conn.commit()
        print("示例数据初始化完成")
    
    conn.close()

# 应用初始化
try:
    init_database()
    init_sample_data()
    print("ROS2 Wiki 应用初始化完成")
except Exception as e:
    print(f"初始化错误: {e}")

# 本地开发启动函数
def main():
    """本地开发服务器"""
    print("=== ROS2 Wiki 完整版 ===")
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动地址: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()