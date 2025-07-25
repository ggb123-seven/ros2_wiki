from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import markdown
import os
import psycopg2
from urllib.parse import urlparse
from datetime import datetime

app = Flask(__name__)

# 环境变量配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')
app.config['DATABASE'] = 'ros2_wiki.db' if not app.config['DATABASE_URL'] else None

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

def init_db():
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
        # PostgreSQL语法
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
        # SQLite语法
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
        # PostgreSQL语法
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
        # SQLite语法
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

# 管理员装饰器
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('需要管理员权限')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 路由
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, u.username 
        FROM documents d 
        LEFT JOIN users u ON d.author_id = u.id 
        ORDER BY d.created_at DESC
    ''')
    documents = cursor.fetchall()
    conn.close()
    return render_template('index.html', documents=documents)

@app.route('/login', methods=['GET', 'POST'])
def login():
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
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # 检查用户是否已存在
        cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            flash('用户名或邮箱已存在')
            conn.close()
            return render_template('register.html')
        
        # 创建新用户
        password_hash = generate_password_hash(password)
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
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/documents/<int:doc_id>/render-html')
def render_document(doc_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    document = cursor.fetchone()
    conn.close()
    
    if not document:
        return jsonify({'error': '文档不存在'}), 404
    
    # 将Markdown转换为HTML
    html_content = markdown.markdown(document[2], extensions=['codehilite', 'fenced_code'])
    
    return jsonify({
        'id': document[0],
        'title': document[1],
        'html_content': html_content,
        'category': document[4],
        'created_at': document[5]
    })

@app.route('/document/<int:doc_id>')
def view_document(doc_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # 获取文档
    cursor.execute('''
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
        WHERE c.document_id = ? 
        ORDER BY c.created_at DESC
    ''', (doc_id,))
    comments = cursor.fetchall()
    
    conn.close()
    
    return render_template('document.html', document=document, comments=comments)

@app.route('/add_comment/<int:doc_id>', methods=['POST'])
@login_required
def add_comment(doc_id):
    content = request.form['content']
    
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comments (document_id, user_id, content) VALUES (?, ?, ?)',
                  (doc_id, current_user.id, content))
    conn.commit()
    conn.close()
    
    flash('评论添加成功')
    return redirect(url_for('view_document', doc_id=doc_id))

# 管理员后台
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # 获取所有文档
    cursor.execute('''
        SELECT d.*, u.username 
        FROM documents d 
        LEFT JOIN users u ON d.author_id = u.id 
        ORDER BY d.created_at DESC
    ''')
    documents = cursor.fetchall()
    
    # 获取统计信息
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM documents')
    doc_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM comments')
    comment_count = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         documents=documents,
                         user_count=user_count,
                         doc_count=doc_count,
                         comment_count=comment_count)

# 管理员上传文档
@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def admin_upload():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form.get('category', 'ROS2基础')
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (title, content, author_id, category) 
            VALUES (?, ?, ?, ?)
        ''', (title, content, current_user.id, category))
        conn.commit()
        conn.close()
        
        flash('文档上传成功')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/upload.html')

# 管理员编辑文档
@app.route('/admin/edit/<int:doc_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit(doc_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form.get('category', 'ROS2基础')
        
        cursor.execute('''
            UPDATE documents 
            SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, content, category, doc_id))
        conn.commit()
        conn.close()
        
        flash('文档更新成功')
        return redirect(url_for('admin_dashboard'))
    
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    document = cursor.fetchone()
    conn.close()
    
    if not document:
        flash('文档不存在')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit.html', document=document)

# 管理员删除文档
@app.route('/admin/delete/<int:doc_id>')
@admin_required
def admin_delete(doc_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # 先删除相关评论
    cursor.execute('DELETE FROM comments WHERE document_id = ?', (doc_id,))
    # 再删除文档
    cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    
    conn.commit()
    conn.close()
    
    flash('文档删除成功')
    return redirect(url_for('admin_dashboard'))

# 确保数据库初始化
init_db()

# 如果数据库为空，添加示例数据
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        # 添加默认用户
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        
        admin_hash = generate_password_hash(admin_password)
        user_hash = generate_password_hash('user123')
        
        if app.config['DATABASE_URL']:
            # PostgreSQL语法
            cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)',
                          (admin_username, admin_email, admin_hash, True))
            cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)',
                          ('ros2_learner', 'user@example.com', user_hash, False))
            
            # 添加示例文档
            cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (%s, %s, %s, %s)',
                          ('ROS2快速入门', '# ROS2快速入门\n\n欢迎来到ROS2世界！', 1, 'ROS2基础'))
        else:
            # SQLite语法
            cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                          (admin_username, admin_email, admin_hash, 1))
            cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                          ('ros2_learner', 'user@example.com', user_hash, 0))
            
            # 添加示例文档
            cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (?, ?, ?, ?)',
                          ('ROS2快速入门', '# ROS2快速入门\n\n欢迎来到ROS2世界！', 1, 'ROS2基础'))
        
        conn.commit()
        print("数据库初始化完成")
    
    conn.close()
except Exception as e:
    print(f"数据库初始化错误: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)