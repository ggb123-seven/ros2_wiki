#!/usr/bin/env python3
"""
Render平台SQLite版本 - 避免PostgreSQL兼容性问题
米醋电子工作室
"""

import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE'] = 'ros2_wiki.db'

# 配置Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 用户类
class User(UserMixin):
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

# 数据库连接
def get_db():
    """获取数据库连接"""
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

# 初始化数据库
def init_db():
    """初始化数据库表"""
    db = get_db()
    cursor = db.cursor()
    
    # 创建用户表
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
    
    # 创建文档表
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
    
    db.commit()
    
    # 创建管理员账户（如果不存在）
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    cursor.execute('SELECT id FROM users WHERE username = ?', (admin_username,))
    if not cursor.fetchone():
        password_hash = generate_password_hash(admin_password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (admin_username, admin_email, password_hash, True))
        db.commit()
        logger.info(f"创建管理员账户: {admin_username}")
    
    db.close()

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    db.close()
    
    if user_data:
        return User(user_data['id'], user_data['username'], 
                   user_data['email'], user_data['is_admin'])
    return None

@app.route('/')
def index():
    """首页"""
    db = get_db()
    cursor = db.cursor()
    
    # 获取最新文档
    cursor.execute('''
        SELECT d.*, u.username as author_name
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        ORDER BY d.created_at DESC
        LIMIT 10
    ''')
    recent_docs = cursor.fetchall()
    
    # 获取分类
    cursor.execute('SELECT DISTINCT category FROM documents')
    categories = [row['category'] for row in cursor.fetchall()]
    
    db.close()
    
    return render_template('index.html', 
                         recent_docs=recent_docs,
                         categories=categories)

@app.route('/health')
def health():
    """健康检查"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        db.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'sqlite',
            'users': user_count
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        db.close()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], 
                       user_data['email'], user_data['is_admin'])
            login_user(user)
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已成功退出', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 密码强度检查
        min_length = int(os.environ.get('MIN_PASSWORD_LENGTH', '8'))
        if len(password) < min_length:
            flash(f'密码长度至少需要{min_length}个字符', 'error')
            return render_template('register.html')
        
        db = get_db()
        cursor = db.cursor()
        
        # 检查用户名是否存在
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('用户名已存在', 'error')
            db.close()
            return render_template('register.html')
        
        # 创建新用户
        password_hash = generate_password_hash(password)
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            db.commit()
            flash('注册成功！请登录', 'success')
            db.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('邮箱已被使用', 'error')
            db.close()
    
    return render_template('register.html')

@app.route('/documents')
def documents():
    """文档列表"""
    db = get_db()
    cursor = db.cursor()
    
    category = request.args.get('category')
    if category:
        cursor.execute('''
            SELECT d.*, u.username as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.category = ?
            ORDER BY d.created_at DESC
        ''', (category,))
    else:
        cursor.execute('''
            SELECT d.*, u.username as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.id
            ORDER BY d.created_at DESC
        ''')
    
    docs = cursor.fetchall()
    db.close()
    
    return render_template('documents.html', documents=docs)

@app.before_request
def before_request():
    """请求前初始化数据库（如果需要）"""
    if not os.path.exists(app.config['DATABASE']):
        init_db()

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 运行应用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)