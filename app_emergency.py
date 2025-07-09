#!/usr/bin/env python3
"""
ROS2 Wiki - 紧急修复版本
直接解决管理员后台问题，不依赖模板
"""

import os
import sys
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
from functools import wraps

# 条件导入psycopg2
try:
    import psycopg2
    HAS_POSTGRESQL = True
except ImportError:
    HAS_POSTGRESQL = False

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

def get_db_connection():
    """获取数据库连接"""
    if app.config['DATABASE_URL'] and HAS_POSTGRESQL:
        return psycopg2.connect(app.config['DATABASE_URL'])
    else:
        return sqlite3.connect(app.config['DATABASE'] or 'ros2_wiki.db')

def init_database():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
    
    # 用户表
    if use_postgresql:
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
    if use_postgresql:
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
    
    conn.commit()
    conn.close()

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
    
    if use_postgresql:
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    else:
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[4] if len(user) > 4 else False)
    return None

def admin_required(f):
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
    """首页"""
    try:
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
    except Exception as e:
        return f"<h1>欢迎来到ROS2 Wiki</h1><p>数据库错误: {e}</p>"

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'ROS2 Wiki 运行正常',
        'database': 'PostgreSQL' if (app.config['DATABASE_URL'] and HAS_POSTGRESQL) else 'SQLite'
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
        
        if use_postgresql:
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
    
    try:
        return render_template('login.html')
    except:
        return f'''
        <form method="post">
            <h2>登录</h2>
            <input type="text" name="username" placeholder="用户名" required>
            <input type="password" name="password" placeholder="密码" required>
            <button type="submit">登录</button>
        </form>
        <p>管理员: admin/admin123</p>
        '''

@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """管理员后台 - 简化版本"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取统计信息
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM documents')
        doc_count = cursor.fetchone()[0]
        
        # 获取最新文档
        cursor.execute('''
            SELECT d.*, u.username 
            FROM documents d 
            LEFT JOIN users u ON d.author_id = u.id 
            ORDER BY d.created_at DESC
            LIMIT 5
        ''')
        recent_docs = cursor.fetchall()
        
        conn.close()
        
        # 生成简单的HTML页面
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ROS2 Wiki 管理后台</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h1>🤖 ROS2 Wiki 管理后台</h1>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5>用户数量</h5>
                                <h2 class="text-primary">{user_count}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5>文档数量</h5>
                                <h2 class="text-success">{doc_count}</h2>
                            </div>
                        </div>
                    </div>
                </div>
                
                <h3>最新文档</h3>
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>标题</th>
                                <th>作者</th>
                                <th>创建时间</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for doc in recent_docs:
            html += f'''
                            <tr>
                                <td>{doc[0]}</td>
                                <td>{doc[1]}</td>
                                <td>{doc[7] if len(doc) > 7 and doc[7] else '管理员'}</td>
                                <td>{doc[5] if len(doc) > 5 else 'N/A'}</td>
                            </tr>
            '''
        
        html += '''
                        </tbody>
                    </table>
                </div>
                
                <div class="mt-4">
                    <a href="/" class="btn btn-primary">返回首页</a>
                    <a href="/health" class="btn btn-info">系统状态</a>
                    <a href="/logout" class="btn btn-secondary">退出登录</a>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        return f'''
        <div class="container mt-4">
            <div class="alert alert-danger">
                <h4>管理员后台错误</h4>
                <p>错误: {str(e)}</p>
                <p>用户: {current_user.username if current_user.is_authenticated else 'Anonymous'}</p>
            </div>
            <a href="/" class="btn btn-primary">返回首页</a>
        </div>
        '''

# 初始化数据库和示例数据
def init_sample_data():
    """初始化示例数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@ros2wiki.com')
            
            admin_hash = generate_password_hash(admin_password)
            
            if use_postgresql:
                cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)',
                              (admin_username, admin_email, admin_hash, True))
                cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (%s, %s, %s, %s)',
                              ('ROS2快速入门', '# ROS2快速入门\n\n欢迎学习ROS2！', 1, 'ROS2基础'))
            else:
                cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                              (admin_username, admin_email, admin_hash, 1))
                cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (?, ?, ?, ?)',
                              ('ROS2快速入门', '# ROS2快速入门\n\n欢迎学习ROS2！', 1, 'ROS2基础'))
            
            conn.commit()
            print("示例数据初始化完成")
        
        conn.close()
    except Exception as e:
        print(f"示例数据初始化错误: {e}")

# 应用初始化
try:
    init_database()
    init_sample_data()
    print("ROS2 Wiki 紧急修复版本初始化完成")
except Exception as e:
    print(f"初始化错误: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)