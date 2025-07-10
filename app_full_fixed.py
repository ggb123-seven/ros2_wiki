#!/usr/bin/env python3
"""
ROS2 Wiki - 修复版完整Flask应用
解决架构冲突，统一使用原生SQLite，添加完整功能
"""

import os
import sys
import sqlite3
import hashlib
import re
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

# 尝试导入Flask相关包，如果失败则使用简化版本
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
    from werkzeug.security import generate_password_hash, check_password_hash
    import markdown
    from markupsafe import Markup
    FLASK_AVAILABLE = True
except ImportError:
    print("Flask依赖不可用，请检查安装")
    FLASK_AVAILABLE = False
    sys.exit(1)

# 创建Flask应用实例
app = Flask(__name__)

# 环境变量配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ros2-wiki-secret-key-2024')
app.config['DATABASE'] = 'ros2_wiki.db'

# 数据库连接函数
def get_db_connection():
    """获取SQLite数据库连接"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
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

# 用户管理类
class User:
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin
        
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_active(self):
        return True
        
    @property
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)
    
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

# 简化的登录装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('需要登录')
            return redirect(url_for('login'))
        
        user = User.get(session['user_id'])
        if not user or not user.is_admin:
            flash('需要管理员权限')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前用户"""
    if 'user_id' in session:
        return User.get(session['user_id'])
    return None

# 模板上下文处理器
@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.authenticate(username, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'欢迎回来，{user.username}！')
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
        
        # 验证输入
        if len(username) < 3:
            flash('用户名至少3个字符')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('密码至少6个字符')
            return render_template('register.html')
        
        conn = get_db_connection()
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
    """用户登出"""
    session.clear()
    flash('已退出登录')
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
    
    # 渲染Markdown内容
    md = markdown.Markdown(extensions=['codehilite', 'fenced_code'])
    html_content = md.convert(document['content'])
    
    return render_template('document.html', 
                         document=document, 
                         comments=comments,
                         html_content=Markup(html_content))

@app.route('/document/<int:doc_id>/comment', methods=['POST'])
@login_required
def add_comment(doc_id):
    """添加评论"""
    content = request.form['content']
    user = get_current_user()
    
    if not content.strip():
        flash('评论内容不能为空')
        return redirect(url_for('view_document', doc_id=doc_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comments (document_id, user_id, content) VALUES (?, ?, ?)',
                  (doc_id, user.id, content))
    conn.commit()
    conn.close()
    
    flash('评论添加成功')
    return redirect(url_for('view_document', doc_id=doc_id))

@app.route('/search')
def search():
    """搜索功能"""
    query = request.args.get('q', '').strip()
    documents = []
    
    if query:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, u.username 
            FROM documents d 
            LEFT JOIN users u ON d.author_id = u.id 
            WHERE d.title LIKE ? OR d.content LIKE ?
            ORDER BY d.created_at DESC
        ''', (f'%{query}%', f'%{query}%'))
        documents = cursor.fetchall()
        conn.close()
    
    return render_template('search/results.html', 
                         documents=documents, 
                         query=query)

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

@app.route('/admin/document/new', methods=['GET', 'POST'])
@admin_required
def admin_new_document():
    """管理员新建文档"""
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        user = get_current_user()
        
        if not title.strip() or not content.strip():
            flash('标题和内容不能为空')
            return render_template('admin/edit.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (title, content, author_id, category) 
            VALUES (?, ?, ?, ?)
        ''', (title, content, user.id, category))
        conn.commit()
        conn.close()
        
        flash('文档创建成功')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit.html')

@app.route('/admin/document/<int:doc_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_document(doc_id):
    """管理员编辑文档"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        
        cursor.execute('''
            UPDATE documents 
            SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, content, category, doc_id))
        conn.commit()
        conn.close()
        
        flash('文档更新成功')
        return redirect(url_for('admin_dashboard'))
    
    # GET请求，获取文档数据
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    document = cursor.fetchone()
    conn.close()
    
    if not document:
        flash('文档不存在')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit.html', document=document)

@app.route('/health')
def health():
    """健康检查端点"""
    return jsonify({
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
    })

@app.route('/api/documents')
def api_documents():
    """API: 获取文档列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.id, d.title, d.category, d.created_at, u.username
        FROM documents d 
        LEFT JOIN users u ON d.author_id = u.id 
        ORDER BY d.created_at DESC
    ''')
    documents = cursor.fetchall()
    conn.close()
    
    return jsonify([dict(doc) for doc in documents])

@app.route('/api/documents/<int:doc_id>/render-html')
def api_render_document(doc_id):
    """API: 渲染文档HTML"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    document = cursor.fetchone()
    conn.close()
    
    if not document:
        return jsonify({'error': '文档不存在'}), 404
    
    # 渲染Markdown
    md = markdown.Markdown(extensions=['codehilite', 'fenced_code'])
    html_content = md.convert(document['content'])
    
    return jsonify({
        'id': document['id'],
        'title': document['title'],
        'html_content': html_content,
        'category': document['category'],
        'created_at': document['created_at']
    })

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
        cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                      (admin_username, admin_email, admin_hash, 1))
        
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

### Ubuntu 22.04 (推荐)

```bash
# 设置源
sudo apt update && sudo apt install curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# 添加仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 安装ROS2
sudo apt update
sudo apt install ros-humble-desktop
```

### 环境配置

```bash
# 设置环境变量
source /opt/ros/humble/setup.bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# 安装colcon构建工具
sudo apt install python3-colcon-common-extensions
```

## 创建第一个工作空间

```bash
# 创建工作空间
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws

# 构建工作空间
colcon build

# 激活工作空间
source install/setup.bash
```

## 第一个ROS2节点

创建一个简单的发布者节点：

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class HelloWorldPublisher(Node):
    def __init__(self):
        super().__init__('hello_world_publisher')
        self.publisher_ = self.create_publisher(String, 'hello_topic', 10)
        self.timer = self.create_timer(1.0, self.publish_message)
        self.counter = 0

    def publish_message(self):
        msg = String()
        msg.data = f'Hello ROS2! Message {self.counter}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')
        self.counter += 1

def main(args=None):
    rclpy.init(args=args)
    node = HelloWorldPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## 下一步学习

1. **话题通信**：学习发布者和订阅者模式
2. **服务调用**：请求-响应通信机制
3. **参数系统**：动态配置节点参数
4. **Launch文件**：批量启动和配置节点
5. **自定义消息**：创建项目专用的数据类型

开始您的ROS2学习之旅！'''
        
        cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (?, ?, ?, ?)',
                      ('ROS2快速入门指南', sample_content, 1, 'ROS2基础'))
        
        # 更多示例文档
        topic_content = '''# ROS2话题通信详解

ROS2的话题（Topic）是节点间异步通信的基础机制。

## 核心概念

- **发布者（Publisher）**：发送消息的节点
- **订阅者（Subscriber）**：接收消息的节点  
- **消息（Message）**：传输的数据结构
- **话题（Topic）**：消息传输的命名通道

## 发布者示例

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SimplePublisher(Node):
    def __init__(self):
        super().__init__('simple_publisher')
        self.publisher_ = self.create_publisher(String, 'chatter', 10)
        self.timer = self.create_timer(0.5, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello World: {self.i}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.i += 1
```

## 订阅者示例

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SimpleSubscriber(Node):
    def __init__(self):
        super().__init__('simple_subscriber')
        self.subscription = self.create_subscription(
            String,
            'chatter',
            self.listener_callback,
            10)

    def listener_callback(self, msg):
        self.get_logger().info(f'I heard: "{msg.data}"')
```

## 常用命令

```bash
# 查看活跃话题
ros2 topic list

# 查看话题信息
ros2 topic info /chatter

# 监听话题消息
ros2 topic echo /chatter

# 发布消息
ros2 topic pub /chatter std_msgs/String "data: 'Hello from command line'"
```

话题通信是ROS2的核心，掌握它是进一步学习的基础！'''
        
        cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (?, ?, ?, ?)',
                      ('ROS2话题通信详解', topic_content, 1, 'ROS2基础'))
        
        conn.commit()
        print("✅ 示例数据初始化完成")
    
    conn.close()

# 应用初始化
try:
    init_database()
    init_sample_data()
    print("✅ ROS2 Wiki 应用初始化完成")
except Exception as e:
    print(f"❌ 初始化错误: {e}")

def main():
    """本地开发服务器"""
    print("=== ROS2 Wiki 完整版（修复版） ===")
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动地址: http://localhost:{port}")
    print(f"👤 默认管理员: admin / admin123")
    print(f"👤 测试用户: ros2_user / user123")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()