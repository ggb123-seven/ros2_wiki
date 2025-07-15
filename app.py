#!/usr/bin/env python3
"""
ROS2 Wiki - 完整版Flask应用
整合所有功能：用户管理、文档系统、搜索、CMS等
"""

import os
import sys
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
from functools import wraps

# 条件导入psycopg2，避免在没有PostgreSQL时出错
try:
    import psycopg2
    import psycopg2.extras
    HAS_POSTGRESQL = True
    print("✅ PostgreSQL driver (psycopg2) loaded successfully")
except ImportError as e:
    HAS_POSTGRESQL = False
    print(f"Warning: psycopg2 not available ({e}), using SQLite only")

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

# 注册蓝图
from app_blueprints.permissions import permissions_bp
app.register_blueprint(permissions_bp)

class User(UserMixin):
    # 初始化用户类
    def __init__(self, id, username, email, is_admin=False, is_blacklisted=False):
        # 初始化用户ID
        self.id = id
        # 初始化用户名
        self.username = username
        # 初始化用户邮箱
        self.email = email
        # 初始化用户是否为管理员，默认为False
        self.is_admin = is_admin
        # 初始化用户是否被拉黑，默认为False
        self.is_blacklisted = is_blacklisted

@login_manager.user_loader
# 定义一个函数，用于加载用户信息
def load_user(user_id):
    # 获取数据库连接
    conn = get_db_connection()
    # 创建游标
    cursor = conn.cursor()
    # 判断是否使用PostgreSQL数据库
    use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
    
    # 如果使用PostgreSQL数据库
    if use_postgresql:
        # 执行SQL查询语句，获取用户信息
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    # 否则
    else:
        # 执行SQL查询语句，获取用户信息
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    # 获取查询结果
    user = cursor.fetchone()
    # 关闭数据库连接
    conn.close()
    # 如果查询结果不为空
    if user:
        # 返回用户信息，包含黑名单状态
        # 字段顺序: id, username, email, password_hash, is_admin, created_at, is_blacklisted, ...
        is_admin = user[4] if len(user) > 4 else False
        is_blacklisted = user[6] if len(user) > 6 else False
        return User(user[0], user[1], user[2], is_admin, is_blacklisted)
    # 否则返回None
    return None

def get_db_connection():
    """获取数据库连接"""
    # 如果使用PostgreSQL数据库并且psycopg2可用
    if app.config['DATABASE_URL'] and HAS_POSTGRESQL:
        # PostgreSQL连接
        return psycopg2.connect(app.config['DATABASE_URL'])
    else:
        # SQLite连接（回退选项）
        if app.config['DATABASE_URL'] and not HAS_POSTGRESQL:
            print("Warning: PostgreSQL URL provided but psycopg2 not available, using SQLite")
        return sqlite3.connect(app.config['DATABASE'] or 'ros2_wiki.db')

def init_database():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 判断是否使用PostgreSQL
    use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
    
    # 用户表
    if use_postgresql:
        # PostgreSQL语法
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                is_blacklisted BOOLEAN DEFAULT FALSE,
                blacklisted_at TIMESTAMP NULL,
                blacklist_reason TEXT NULL,
                last_seen TIMESTAMP NULL,
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
                is_blacklisted BOOLEAN DEFAULT 0,
                blacklisted_at TIMESTAMP NULL,
                blacklist_reason TEXT NULL,
                last_seen TIMESTAMP NULL,
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
    
    # 评论表
    if use_postgresql:
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

    # 用户操作日志表
    if use_postgresql:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_logs (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER REFERENCES users(id),
                target_user_id INTEGER REFERENCES users(id),
                action TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                target_user_id INTEGER,
                action TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users (id),
                FOREIGN KEY (target_user_id) REFERENCES users (id)
            )
        ''')

    conn.commit()

    # 检查是否需要创建默认数据
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        # 创建云端管理员账户（优先）
        cloud_admin_username = os.environ.get('ADMIN_USERNAME', 'ssss')
        cloud_admin_email = os.environ.get('ADMIN_EMAIL', 'seventee_0611@qq.com')
        cloud_admin_password = os.environ.get('ADMIN_PASSWORD', 'ssss123')

        if os.environ.get('AUTO_CREATE_ADMIN', 'false').lower() == 'true':
            admin_password_hash = generate_password_hash(cloud_admin_password)
            if use_postgresql:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin)
                    VALUES (%s, %s, %s, %s)
                ''', (cloud_admin_username, cloud_admin_email, admin_password_hash, True))
            else:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin)
                    VALUES (?, ?, ?, ?)
                ''', (cloud_admin_username, cloud_admin_email, admin_password_hash, True))
            print(f"✅ Created cloud admin account: {cloud_admin_username}")

        # 创建默认管理员用户（备用）
        admin_password = generate_password_hash('admin123')
        if use_postgresql:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (%s, %s, %s, %s)
            ''', ('ros2_admin', 'admin@ros2wiki.com', admin_password, True))
        else:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('ros2_admin', 'admin@ros2wiki.com', admin_password, True))

        # 创建测试用户
        user_password = generate_password_hash('user123')
        if use_postgresql:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (%s, %s, %s, %s)
            ''', ('ros2_user', 'user@ros2wiki.com', user_password, False))
        else:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('ros2_user', 'user@ros2wiki.com', user_password, False))

        # 创建示例文档
        cursor.execute('''
            INSERT INTO documents (title, content, category, author_id)
            VALUES (?, ?, ?, ?)
        ''', ('ROS2入门教程', '''# ROS2入门教程

## 什么是ROS2？

ROS2（Robot Operating System 2）是一个开源的机器人操作系统框架，专为现代机器人应用设计。

## 主要特性

- **实时性能**：支持实时系统要求
- **安全性**：内置安全机制
- **跨平台**：支持Linux、Windows、macOS
- **分布式架构**：支持多机器人协作

## 安装指南

### Ubuntu 22.04 安装

```bash
# 设置locale
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 添加ROS2 apt源
sudo apt update && sudo apt install curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 安装ROS2
sudo apt update
sudo apt install ros-humble-desktop
```

## 下一步

完成安装后，您可以继续学习：
- 创建工作空间
- 编写第一个节点
- 学习话题通信
''', '基础教程', 1))

        cursor.execute('''
            INSERT INTO documents (title, content, category, author_id)
            VALUES (?, ?, ?, ?)
        ''', ('ROS2节点通信', '''# ROS2节点通信

## 话题通信（Topics）

话题是ROS2中最常用的通信方式，采用发布-订阅模式。

### 创建发布者

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = 'Hello World: %d' % self.i
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)
        self.i += 1

def main(args=None):
    rclpy.init(args=args)
    minimal_publisher = MinimalPublisher()
    rclpy.spin(minimal_publisher)
    minimal_publisher.destroy_node()
    rclpy.shutdown()
```

### 创建订阅者

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10)

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg.data)

def main(args=None):
    rclpy.init(args=args)
    minimal_subscriber = MinimalSubscriber()
    rclpy.spin(minimal_subscriber)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()
```

## 服务通信（Services）

服务提供同步的请求-响应通信模式。

## 动作通信（Actions）

动作用于长时间运行的任务，提供反馈机制。
''', '进阶教程', 1))

        cursor.execute('''
            INSERT INTO documents (title, content, category, author_id)
            VALUES (?, ?, ?, ?)
        ''', ('ROS2工作空间管理', '''# ROS2工作空间管理

## 创建工作空间

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
```

## 包管理

### 创建包

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python my_package
```

### 编译包

```bash
cd ~/ros2_ws
colcon build --packages-select my_package
```

## 环境设置

```bash
source ~/ros2_ws/install/setup.bash
```
''', '工具使用', 1))

        conn.commit()
        print("✅ 默认用户和示例文档已创建")

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

# 统计功能函数
def get_homepage_stats():
    """获取首页统计数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 重用现有的统计查询模式
        cursor.execute('SELECT COUNT(*) FROM documents')
        doc_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT category) FROM documents WHERE category IS NOT NULL')
        category_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM comments')
        comment_count = cursor.fetchone()[0]

        conn.close()

        return {
            'doc_count': doc_count,
            'category_count': category_count,
            'user_count': user_count,
            'comment_count': comment_count
        }
    except Exception as e:
        print(f"统计数据获取错误: {e}")
        return {
            'doc_count': 0,
            'category_count': 0,
            'user_count': 0,
            'comment_count': 0
        }

# 路由定义
@app.route('/')
def index():
    """首页 - 未登录用户显示登录界面，已登录用户显示现代化文档首页"""
    # 如果用户未登录，重定向到登录页面
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    # 已登录用户显示现代化首页
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取最新文档
    cursor.execute('''
        SELECT d.*, u.username as author_name
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        ORDER BY d.created_at DESC
        LIMIT 6
    ''')
    latest_docs = cursor.fetchall()

    # 转换为字典格式以便模板使用
    latest_docs_list = []
    for doc in latest_docs:
        doc_dict = {
            'id': doc[0],
            'title': doc[1],
            'content': doc[2],
            'author_id': doc[3],
            'category': doc[4],
            'created_at': doc[5],
            'updated_at': doc[6],
            'author_name': doc[7] if len(doc) > 7 else '系统'
        }
        # 处理日期格式
        if isinstance(doc_dict['created_at'], str):
            from datetime import datetime
            doc_dict['created_at'] = datetime.strptime(doc_dict['created_at'], '%Y-%m-%d %H:%M:%S')
        latest_docs_list.append(doc_dict)

    conn.close()

    # 获取统计数据
    stats = get_homepage_stats()

    # 计算运行天数
    from datetime import datetime, date
    launch_date = date(2024, 1, 1)  # 假设启动日期
    today = date.today()
    days_since_launch = (today - launch_date).days

    # 准备统计数据
    stats_data = {
        'total_documents': stats.get('doc_count', 0),
        'total_users': stats.get('user_count', 0),
        'total_views': stats.get('doc_count', 0) * 127,  # 模拟浏览量
        'days_since_launch': days_since_launch
    }

    return render_template('modern_index.html',
                         latest_docs=latest_docs_list,
                         stats=stats_data)

@app.route('/documents')
@login_required
def documents():
    """文档列表页面 - 支持搜索、分页、筛选"""
    # 获取查询参数
    page = int(request.args.get('page', 1))
    per_page = 12  # 每页显示12个文档
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    sort = request.args.get('sort', 'newest')

    conn = get_db_connection()
    cursor = conn.cursor()
    use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL

    # 构建查询条件
    where_conditions = []
    params = []

    if search:
        where_conditions.append("(d.title LIKE ? OR d.content LIKE ?)")
        params.extend([f'%{search}%', f'%{search}%'])

    if category:
        where_conditions.append("d.category = ?")
        params.append(category)

    where_clause = " AND ".join(where_conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    # 排序逻辑
    if sort == 'oldest':
        order_clause = "ORDER BY d.created_at ASC"
    elif sort == 'title':
        order_clause = "ORDER BY d.title ASC"
    else:  # newest
        order_clause = "ORDER BY d.created_at DESC"

    # 获取总数
    count_query = f'''
        SELECT COUNT(*)
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        {where_clause}
    '''
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    # 计算分页
    total_pages = (total_count + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # 获取文档数据
    query = f'''
        SELECT d.*, u.username as author_name
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        {where_clause}
        {order_clause}
        LIMIT ? OFFSET ?
    '''
    cursor.execute(query, params + [per_page, offset])
    all_docs = cursor.fetchall()

    # 转换为字典格式
    docs_list = []
    for doc in all_docs:
        doc_dict = {
            'id': doc[0],
            'title': doc[1],
            'content': doc[2],
            'author_id': doc[3],
            'category': doc[4],
            'created_at': doc[5],
            'updated_at': doc[6],
            'author_name': doc[7] if len(doc) > 7 else '系统'
        }
        # 处理日期格式
        if isinstance(doc_dict['created_at'], str):
            from datetime import datetime
            doc_dict['created_at'] = datetime.strptime(doc_dict['created_at'], '%Y-%m-%d %H:%M:%S')
        docs_list.append(doc_dict)

    conn.close()

    return render_template('documents_list.html',
                         documents=docs_list,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count)

@app.route('/admin/new_document')
@admin_required
def admin_new_document():
    """管理员创建新文档"""
    return redirect(url_for('create_document'))

@app.route('/admin/edit_document/<int:doc_id>')
@admin_required
def admin_edit_document(doc_id):
    """管理员编辑文档"""
    return redirect(url_for('edit_document', doc_id=doc_id))

@app.route('/admin/delete_document/<int:doc_id>', methods=['POST'])
@admin_required
def admin_delete_document(doc_id):
    """管理员删除文档"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL

        # 首先检查文档是否存在
        if use_postgresql:
            cursor.execute('SELECT title FROM documents WHERE id = %s', (doc_id,))
        else:
            cursor.execute('SELECT title FROM documents WHERE id = ?', (doc_id,))

        document = cursor.fetchone()
        if not document:
            flash('文档不存在', 'error')
            return redirect(url_for('admin_dashboard'))

        # 删除相关评论
        if use_postgresql:
            cursor.execute('DELETE FROM comments WHERE document_id = %s', (doc_id,))
        else:
            cursor.execute('DELETE FROM comments WHERE document_id = ?', (doc_id,))

        # 删除文档
        if use_postgresql:
            cursor.execute('DELETE FROM documents WHERE id = %s', (doc_id,))
        else:
            cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))

        conn.commit()
        conn.close()

        flash(f'文档 "{document[0]}" 删除成功', 'success')

    except Exception as e:
        flash(f'删除文档失败：{str(e)}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/demo')
def demo_homepage():
    """演示现代化首页"""
    # 模拟数据
    latest_docs_list = [
        {
            'id': 1,
            'title': 'ROS2入门教程',
            'content': 'ROS2（Robot Operating System 2）是一个开源的机器人操作系统框架，专为现代机器人应用设计。',
            'category': '基础教程',
            'created_at': datetime.now(),
            'author_name': 'ros2_admin'
        },
        {
            'id': 2,
            'title': 'ROS2节点通信',
            'content': '话题是ROS2中最常用的通信方式，采用发布-订阅模式。',
            'category': '进阶教程',
            'created_at': datetime.now(),
            'author_name': 'ros2_admin'
        },
        {
            'id': 3,
            'title': 'ROS2工作空间管理',
            'content': '创建工作空间是ROS2开发的第一步。',
            'category': '工具使用',
            'created_at': datetime.now(),
            'author_name': 'ros2_admin'
        }
    ]

    # 统计数据
    stats_data = {
        'total_documents': 45,
        'total_users': 951,
        'total_views': 17094,
        'days_since_launch': 113
    }

    return render_template('modern_index.html',
                         latest_docs=latest_docs_list,
                         stats=stats_data)

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

@app.route('/search')
def search():
    """搜索功能"""
    # 获取搜索关键字
    query = request.args.get('q', '').strip()
    # 如果没有搜索关键字，则返回空结果
    if not query:
        return render_template('search.html', results=[], query='')

    # 获取数据库连接
    conn = get_db_connection()
    cursor = conn.cursor()

    # 简单的搜索实现
    # 构造搜索模式，包含关键字
    search_pattern = f"%{query}%"
    # 执行SQL查询，搜索标题或内容中包含关键字的文档
    cursor.execute('''
        SELECT d.*, u.username
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        WHERE d.title LIKE ? OR d.content LIKE ?
        ORDER BY d.created_at DESC
        LIMIT 20
    ''', [search_pattern, search_pattern])

    # 获取查询结果
    results = cursor.fetchall()
    # 关闭数据库连接
    conn.close()

    # 返回搜索结果页面
    return render_template('search.html', results=results, query=query)

@app.route('/stats-test')
def stats_test():
    """测试统计功能性能"""
    import time
    start_time = time.time()
    stats = get_homepage_stats()
    end_time = time.time()
    execution_time = (end_time - start_time) * 1000  # 转换为毫秒

    return jsonify({
        'stats': stats,
        'performance': {
            'execution_time_ms': round(execution_time, 2),
            'status': 'fast' if execution_time < 100 else 'slow'
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
    # 判断请求方法是否为POST
    if request.method == 'POST':
        # 获取用户名和密码
        username = request.form['username']
        password = request.form['password']
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        # 判断是否使用PostgreSQL数据库
        use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
        
        # 根据数据库类型执行查询语句
        if use_postgresql:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        else:
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        # 获取查询结果
        user = cursor.fetchone()
        # 关闭数据库连接
        conn.close()
        
        # 判断用户是否存在且密码正确
        if user and check_password_hash(user[3], password):
            # 检查用户是否被拉黑
            # 字段顺序: id, username, email, password_hash, is_admin, created_at, is_blacklisted, ...
            is_blacklisted = user[6] if len(user) > 6 else False
            if is_blacklisted:
                flash('账户已被禁用，请联系管理员')
                return render_template('login.html')

            # 更新用户最后登录时间
            conn = get_db_connection()
            cursor = conn.cursor()
            if use_postgresql:
                cursor.execute('UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = %s', (user[0],))
            else:
                cursor.execute("UPDATE users SET last_seen = datetime('now') WHERE id = ?", (user[0],))
            conn.commit()
            conn.close()

            # 创建用户对象
            is_admin = user[4] if len(user) > 4 else False
            user_obj = User(user[0], user[1], user[2], is_admin, is_blacklisted)
            # 登录用户
            login_user(user_obj)
            # 重定向到首页
            return redirect(url_for('index'))
        else:
            # 提示用户名或密码错误
            flash('用户名或密码错误')
    
    # 渲染登录页面
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
        use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
        
        # 检查用户是否已存在
        if use_postgresql:
            cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, email))
        else:
            cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        
        if cursor.fetchone():
            flash('用户名或邮箱已存在')
            conn.close()
            return render_template('register.html')
        
        # 创建新用户
        password_hash = generate_password_hash(password)
        if use_postgresql:
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
    use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL

    # 获取文档
    if use_postgresql:
        cursor.execute('''
            SELECT d.*, u.username
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.id = %s
        ''', (doc_id,))
    else:
        cursor.execute('''
            SELECT d.*, u.username
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.id = ?
        ''', (doc_id,))
    document_row = cursor.fetchone()

    if not document_row:
        flash('文档不存在')
        return redirect(url_for('index'))

    # 将tuple转换为字典，便于模板访问
    document = {
        'id': document_row[0],
        'title': document_row[1],
        'content': document_row[2],
        'author_id': document_row[3],
        'category': document_row[4],
        'created_at': document_row[5],
        'updated_at': document_row[6],
        'username': document_row[7] if len(document_row) > 7 else '管理员'
    }

    # 渲染Markdown内容
    import markdown
    html_content = markdown.markdown(document['content'], extensions=['codehilite', 'fenced_code'])

    # 获取评论
    if use_postgresql:
        cursor.execute('''
            SELECT c.*, u.username
            FROM comments c
            LEFT JOIN users u ON c.user_id = u.id
            WHERE c.document_id = %s
            ORDER BY c.created_at DESC
        ''', (doc_id,))
    else:
        cursor.execute('''
            SELECT c.*, u.username
            FROM comments c
            LEFT JOIN users u ON c.user_id = u.id
            WHERE c.document_id = ?
            ORDER BY c.created_at DESC
        ''', (doc_id,))
    comments_rows = cursor.fetchall()

    # 将评论也转换为字典
    comments = []
    for comment_row in comments_rows:
        comments.append({
            'id': comment_row[0],
            'content': comment_row[1],
            'user_id': comment_row[2],
            'document_id': comment_row[3],
            'created_at': comment_row[4],
            'username': comment_row[5] if len(comment_row) > 5 else '匿名用户'
        })

    conn.close()

    return render_template('document.html', document=document, comments=comments, html_content=html_content)

@app.route('/document/<int:doc_id>/comment', methods=['POST'])
@login_required
def add_comment(doc_id):
    """添加评论"""
    content = request.form.get('content', '').strip()

    if not content:
        flash('评论内容不能为空')
        return redirect(url_for('view_document', doc_id=doc_id))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL

        if use_postgresql:
            cursor.execute('''
                INSERT INTO comments (content, user_id, document_id)
                VALUES (%s, %s, %s)
            ''', (content, current_user.id, doc_id))
        else:
            cursor.execute('''
                INSERT INTO comments (content, user_id, document_id)
                VALUES (?, ?, ?)
            ''', (content, current_user.id, doc_id))

        conn.commit()
        conn.close()

        flash('评论发表成功！')

    except Exception as e:
        flash(f'评论发表失败：{str(e)}')

    return redirect(url_for('view_document', doc_id=doc_id))

@app.route('/create-document', methods=['GET', 'POST'])
@admin_required
def create_document():
    """创建新文档 - 仅管理员可用"""
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']

        if not title or not content:
            flash('标题和内容不能为空')
            return render_template('create_document.html')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL

            if use_postgresql:
                cursor.execute('''
                    INSERT INTO documents (title, content, author_id, category)
                    VALUES (%s, %s, %s, %s)
                ''', (title, content, current_user.id, category))
            else:
                cursor.execute('''
                    INSERT INTO documents (title, content, author_id, category)
                    VALUES (?, ?, ?, ?)
                ''', (title, content, current_user.id, category))

            conn.commit()
            conn.close()

            flash('文档创建成功！')
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            flash(f'创建文档失败：{str(e)}')
            return render_template('create_document.html')

    return render_template('create_document.html')

@app.route('/edit-document/<int:doc_id>', methods=['GET', 'POST'])
@admin_required
def edit_document(doc_id):
    """编辑文档 - 仅管理员可用"""
    conn = get_db_connection()
    cursor = conn.cursor()
    use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']


        if not title or not content:
            flash('标题和内容不能为空')
            return redirect(url_for('edit_document', doc_id=doc_id))

        try:
            if use_postgresql:
                cursor.execute('''
                    UPDATE documents
                    SET title = %s, content = %s, category = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (title, content, category, doc_id))
            else:
                cursor.execute('''
                    UPDATE documents
                    SET title = ?, content = ?, category = ?, updated_at = datetime('now')
                    WHERE id = ?
                ''', (title, content, category, doc_id))

            conn.commit()
            conn.close()

            flash('文档更新成功！')
            return redirect(url_for('view_document', doc_id=doc_id))

        except Exception as e:
            flash(f'更新文档失败：{str(e)}')
            return redirect(url_for('edit_document', doc_id=doc_id))

    # GET请求 - 显示编辑表单
    try:
        if use_postgresql:
            cursor.execute('SELECT * FROM documents WHERE id = %s', (doc_id,))
        else:
            cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))

        document = cursor.fetchone()
        conn.close()

        if not document:
            flash('文档不存在')
            return redirect(url_for('admin_dashboard'))

        # 转换为字典格式
        doc_dict = {
            'id': document[0],
            'title': document[1],
            'content': document[2],
            'author_id': document[3],
            'category': document[4],
            'created_at': document[5],
            'updated_at': document[6]
        }

        return render_template('edit_document.html', document=doc_dict)

    except Exception as e:
        flash(f'加载文档失败：{str(e)}')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin')
@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    """管理员后台 - 使用模板版本"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取统计信息
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM documents')
        doc_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM comments')
        comment_count = cursor.fetchone()[0]

        # 获取黑名单用户数量
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_blacklisted = 1')
        blacklisted_count = cursor.fetchone()[0]

        # 获取最新注册用户
        cursor.execute('''
            SELECT id, username, email, is_admin, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        recent_users = cursor.fetchall()

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

        # 转换为字典格式便于模板使用
        users_list = []
        for user in recent_users:
            users_list.append({
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'is_admin': user[3],
                'created_at': user[4]
            })

        docs_list = []
        for doc in recent_docs:
            docs_list.append({
                'id': doc[0],
                'title': doc[1],
                'category': doc[4] if len(doc) > 4 else 'N/A',
                'created_at': doc[5] if len(doc) > 5 else 'N/A',
                'username': doc[7] if len(doc) > 7 and doc[7] else 'Unknown'
            })

        return render_template('admin_dashboard.html',
                             user_count=user_count,
                             doc_count=doc_count,
                             comment_count=comment_count,
                             blacklisted_count=blacklisted_count,
                             recent_users=users_list,
                             recent_docs=docs_list)

    except Exception as e:
        flash(f'管理后台加载失败：{str(e)}')
        return redirect(url_for('index'))

# 初始化数据库和示例数据
def init_sample_data():
    """初始化示例数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        use_postgresql = app.config['DATABASE_URL'] and HAS_POSTGRESQL
        
        # 检查是否已有数据
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # 创建默认管理员
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@ros2wiki.com')
            
            admin_hash = generate_password_hash(admin_password)
            
            if use_postgresql:
                cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)',
                              (admin_username, admin_email, admin_hash, True))
                # 添加示例用户
                cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)',
                              ('ros2_user', 'user@ros2wiki.com', generate_password_hash('user123'), False))

                # 添加所有示例教程
                for tutorial in sample_tutorials:
                    cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (%s, %s, %s, %s)',
                                  (tutorial['title'], tutorial['content'], 1, tutorial['category']))
            else:
                cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                              (admin_username, admin_email, admin_hash, 1))
                cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                              ('ros2_user', 'user@ros2wiki.com', generate_password_hash('user123'), 0))

                # 添加所有示例教程
                for tutorial in sample_tutorials:
                    cursor.execute('INSERT INTO documents (title, content, author_id, category) VALUES (?, ?, ?, ?)',
                                  (tutorial['title'], tutorial['content'], 1, tutorial['category']))
            
            conn.commit()
            print("示例数据初始化完成")
        
        conn.close()
    except Exception as e:
        print(f"示例数据初始化错误: {e}")

# 示例教程内容
sample_tutorials = [
    {
        'title': 'ROS2快速入门指南',
        'content': '''# ROS2快速入门指南

## 什么是ROS2？

ROS2（Robot Operating System 2）是一个开源的机器人操作系统，提供了一套工具、库和约定，用于简化复杂和健壮的机器人行为的创建。

## 核心概念

### 1. 节点（Node）
节点是ROS2中最基本的执行单元，每个节点都是一个独立的进程。

```python
import rclpy
from rclpy.node import Node

class MinimalNode(Node):
    def __init__(self):
        super().__init__('minimal_node')
        self.get_logger().info('Hello ROS2!')

def main(args=None):
    rclpy.init(args=args)
    node = MinimalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 2. 话题（Topic）
话题是节点之间进行异步通信的方式。

```python
# 发布者
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class Publisher(Node):
    def __init__(self):
        super().__init__('publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello World: {self.i}'
        self.publisher_.publish(msg)
        self.i += 1
```

## 安装ROS2

### Ubuntu系统安装

```bash
# 添加ROS2仓库
sudo apt update && sudo apt install curl gnupg2 lsb-release
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64,arm64] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'

# 安装ROS2
sudo apt update
sudo apt install ros-humble-desktop
```

### 环境配置

```bash
# 添加到.bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## 创建工作空间

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
source install/setup.bash
```

这就是ROS2的基础入门内容，接下来我们将深入学习更多高级特性。''',
        'category': 'ROS2基础'
    },
    {
        'title': 'ROS2节点通信详解',
        'content': '''# ROS2节点通信详解

## 话题通信（Topic Communication）

话题是ROS2中最常用的通信方式，适用于连续数据流的传输。

### 发布者（Publisher）

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello World: {self.i}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.i += 1

def main(args=None):
    rclpy.init(args=args)
    minimal_publisher = MinimalPublisher()
    rclpy.spin(minimal_publisher)
    minimal_publisher.destroy_node()
    rclpy.shutdown()
```

### 订阅者（Subscriber）

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(f'I heard: "{msg.data}"')

def main(args=None):
    rclpy.init(args=args)
    minimal_subscriber = MinimalSubscriber()
    rclpy.spin(minimal_subscriber)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()
```

## 自定义消息类型

### 创建消息文件

```bash
# 在包的msg目录下创建Num.msg
int64 num
```

### 配置package.xml

```xml
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

### 配置CMakeLists.txt

```cmake
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Num.msg"
)
```

## 质量服务（QoS）

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

qos_profile = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10
)

self.publisher_ = self.create_publisher(String, 'topic', qos_profile)
```

节点通信是ROS2的核心功能，掌握这些概念对于开发机器人应用至关重要。''',
        'category': 'ROS2基础'
    },
    {
        'title': 'ROS2服务通信详解',
        'content': '''# ROS2服务通信详解

## 服务与话题的区别

ROS2中有两种主要的通信方式：
- **话题（Topic）**：异步、多对多通信
- **服务（Service）**：同步、一对一通信

## 创建服务

### 1. 定义服务接口

首先创建一个自定义服务接口：

```python
# tutorial_interfaces/srv/AddTwoInts.srv
int64 a
int64 b
---
int64 sum
```

### 2. 服务端实现

```python
import rclpy
from rclpy.node import Node
from tutorial_interfaces.srv import AddTwoInts

class AddTwoIntsServer(Node):
    def __init__(self):
        super().__init__('add_two_ints_server')
        self.srv = self.create_service(
            AddTwoInts,
            'add_two_ints',
            self.add_two_ints_callback
        )

    def add_two_ints_callback(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info(f'Incoming request: a={request.a} b={request.b}')
        return response

def main(args=None):
    rclpy.init(args=args)
    node = AddTwoIntsServer()
    rclpy.spin(node)
    rclpy.shutdown()
```

### 3. 客户端实现

```python
import rclpy
from rclpy.node import Node
from tutorial_interfaces.srv import AddTwoInts
import sys

class AddTwoIntsClient(Node):
    def __init__(self):
        super().__init__('add_two_ints_client')
        self.cli = self.create_client(AddTwoInts, 'add_two_ints')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting...')
        self.req = AddTwoInts.Request()

    def send_request(self, a, b):
        self.req.a = a
        self.req.b = b
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

def main(args=None):
    rclpy.init(args=args)
    node = AddTwoIntsClient()
    response = node.send_request(int(sys.argv[1]), int(sys.argv[2]))
    node.get_logger().info(f'Result: {response.sum}')
    rclpy.shutdown()
```

## 使用方法

```bash
# 启动服务端
ros2 run tutorial_package add_two_ints_server

# 启动客户端
ros2 run tutorial_package add_two_ints_client 3 5
```

## 服务调试

```bash
# 查看可用服务
ros2 service list

# 查看服务接口
ros2 service type /add_two_ints

# 命令行调用服务
ros2 service call /add_two_ints tutorial_interfaces/srv/AddTwoInts "{a: 1, b: 2}"
```

服务通信是ROS2中实现同步交互的重要方式，适用于需要即时响应的场景。''',
        'category': 'ROS2进阶'
    },
    {
        'title': 'ROS2 Launch文件编写',
        'content': '''# ROS2 Launch文件编写

## Launch文件的作用

Launch文件用于：
- 同时启动多个节点
- 设置节点参数
- 配置节点间的重映射
- 管理复杂的机器人系统

## Python Launch文件

### 基础示例

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='talker'
        ),
        Node(
            package='demo_nodes_py',
            executable='listener',
            name='listener'
        )
    ])
```

### 高级配置

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

def generate_launch_description():
    # 声明参数
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )

    # 获取参数值
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        use_sim_time_arg,

        # 机器人状态发布节点
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'use_sim_time': use_sim_time}]
        ),

        # 条件启动节点
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            condition=IfCondition(use_sim_time)
        ),

        # 启动外部进程
        ExecuteProcess(
            cmd=['ros2', 'bag', 'play', 'rosbag.bag'],
            output='screen'
        )
    ])
```

## XML Launch文件

```xml
<launch>
    <arg name="use_sim_time" default="false"/>

    <node pkg="robot_state_publisher"
          exec="robot_state_publisher"
          name="robot_state_publisher">
        <param name="use_sim_time" value="$(var use_sim_time)"/>
    </node>

    <node pkg="rviz2"
          exec="rviz2"
          name="rviz2"
          if="$(var use_sim_time)"/>
</launch>
```

## 运行Launch文件

```bash
# 运行Python launch文件
ros2 launch my_package my_launch.py

# 运行XML launch文件
ros2 launch my_package my_launch.xml

# 传递参数
ros2 launch my_package my_launch.py use_sim_time:=true
```

Launch文件是管理复杂ROS2系统的重要工具，合理使用能大大提高开发效率。''',
        'category': 'ROS2工具'
    },
    {
        'title': 'ROS2参数服务器使用',
        'content': '''# ROS2参数服务器使用

## 参数系统概述

ROS2的参数系统允许节点存储和检索配置数据，支持动态重配置。

## 声明和使用参数

### 在节点中声明参数

```python
import rclpy
from rclpy.node import Node

class ParameterNode(Node):
    def __init__(self):
        super().__init__('parameter_node')

        # 声明参数
        self.declare_parameter('my_parameter', 'default_value')
        self.declare_parameter('my_int_param', 42)
        self.declare_parameter('my_double_param', 3.14)

        # 获取参数值
        my_param = self.get_parameter('my_parameter').get_parameter_value().string_value
        my_int = self.get_parameter('my_int_param').get_parameter_value().integer_value

        self.get_logger().info(f'Parameter value: {my_param}')
        self.get_logger().info(f'Integer parameter: {my_int}')

        # 创建定时器来定期检查参数
        self.timer = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        my_param = self.get_parameter('my_parameter').get_parameter_value().string_value
        self.get_logger().info(f'Current parameter value: {my_param}')

def main(args=None):
    rclpy.init(args=args)
    node = ParameterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

## 参数回调

```python
from rclpy.parameter import Parameter

class ParameterCallbackNode(Node):
    def __init__(self):
        super().__init__('parameter_callback_node')

        self.declare_parameter('my_parameter', 'default')

        # 设置参数回调
        self.add_on_set_parameters_callback(self.parameter_callback)

    def parameter_callback(self, params):
        for param in params:
            if param.name == 'my_parameter':
                self.get_logger().info(f'Parameter changed: {param.value}')
        return SetParametersResult(successful=True)
```

## 命令行参数操作

```bash
# 列出所有参数
ros2 param list

# 获取参数值
ros2 param get /parameter_node my_parameter

# 设置参数值
ros2 param set /parameter_node my_parameter "new_value"

# 转储参数到文件
ros2 param dump /parameter_node

# 从文件加载参数
ros2 param load /parameter_node params.yaml
```

## 参数文件

### YAML格式

```yaml
parameter_node:
  ros__parameters:
    my_parameter: "hello world"
    my_int_param: 100
    my_double_param: 2.71
    my_bool_param: true
    my_string_array: ["one", "two", "three"]
```

### 在Launch文件中使用

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_package',
            executable='parameter_node',
            name='parameter_node',
            parameters=[
                {'my_parameter': 'launch_value'},
                '/path/to/params.yaml'
            ]
        )
    ])
```

参数系统是ROS2中配置节点行为的重要机制，合理使用可以提高系统的灵活性。''',
        'category': 'ROS2进阶'
    },
    {
        'title': 'ROS2自定义消息和服务',
        'content': '''# ROS2自定义消息和服务

## 创建自定义消息

### 1. 创建包结构

```bash
ros2 pkg create --build-type ament_cmake tutorial_interfaces
cd tutorial_interfaces
mkdir msg srv
```

### 2. 定义消息文件

创建 `msg/Num.msg`:
```
int64 num
```

创建 `msg/Sphere.msg`:
```
geometry_msgs/Point center
float64 radius
```

### 3. 配置CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.8)
project(tutorial_interfaces)

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Num.msg"
  "msg/Sphere.msg"
  "srv/AddThreeInts.srv"
  DEPENDENCIES geometry_msgs
)

ament_package()
```

### 4. 配置package.xml

```xml
<?xml version="1.0"?>
<package format="3">
  <name>tutorial_interfaces</name>
  <version>0.0.0</version>
  <description>Tutorial interfaces package</description>
  <maintainer email="you@domain.tld">Your Name</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <depend>geometry_msgs</depend>

  <build_depend>rosidl_default_generators</build_depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

## 创建自定义服务

### 定义服务文件

创建 `srv/AddThreeInts.srv`:
```
int64 a
int64 b
int64 c
---
int64 sum
```

## 使用自定义接口

### 发布自定义消息

```python
import rclpy
from rclpy.node import Node
from tutorial_interfaces.msg import Num

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(Num, 'topic', 10)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = Num()
        msg.num = self.i
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: {msg.num}')
        self.i += 1

def main(args=None):
    rclpy.init(args=args)
    minimal_publisher = MinimalPublisher()
    rclpy.spin(minimal_publisher)
    minimal_publisher.destroy_node()
    rclpy.shutdown()
```

### 订阅自定义消息

```python
import rclpy
from rclpy.node import Node
from tutorial_interfaces.msg import Num

class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            Num,
            'topic',
            self.listener_callback,
            10)

    def listener_callback(self, msg):
        self.get_logger().info(f'I heard: {msg.num}')

def main(args=None):
    rclpy.init(args=args)
    minimal_subscriber = MinimalSubscriber()
    rclpy.spin(minimal_subscriber)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()
```

## 构建和测试

```bash
# 构建包
colcon build --packages-select tutorial_interfaces

# 源环境
source install/setup.bash

# 测试接口
ros2 interface show tutorial_interfaces/msg/Num
ros2 interface show tutorial_interfaces/srv/AddThreeInts
```

自定义接口是ROS2开发中的重要技能，能够满足特定应用的数据传输需求。''',
        'category': 'ROS2进阶'
    }
]

# 应用初始化
try:
    init_database()
    init_sample_data()
    print("ROS2 Wiki 应用初始化完成")
except Exception as e:
    print(f"初始化错误: {e}")

# 添加云端调试端点
if os.environ.get('FLASK_ENV') == 'production':
    try:
        from cloud_debug_endpoints import add_debug_endpoints
        app = add_debug_endpoints(app)
        print("✅ Cloud debug endpoints enabled")
    except ImportError:
        print("⚠️ Cloud debug endpoints not available")

# 本地开发启动函数
def main():
    """本地开发服务器"""
    print("=== ROS2 Wiki 完整版 ===")
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动地址: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()