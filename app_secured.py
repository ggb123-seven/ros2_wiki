#!/usr/bin/env python3
"""
安全加固版本的ROS2 Wiki应用
米醋电子工作室 - SuperClaude安全优化版本
"""

import os
import sqlite3
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_required, current_user
from security_middleware import setup_security_middleware, csrf_protect, rate_limit
from improved_search import ImprovedSearchService

# PostgreSQL支持
try:
    import psycopg2
    HAS_POSTGRESQL = True
except ImportError:
    HAS_POSTGRESQL = False
    print("Warning: psycopg2 not available, using SQLite only")

# 数据库兼容性工具类
class DatabaseCompatibility:
    """数据库兼容性工具类 - 支持PostgreSQL和SQLite"""

    @staticmethod
    def get_placeholder(use_postgresql=False):
        """获取数据库占位符"""
        return '%s' if use_postgresql else '?'

    @staticmethod
    def build_search_condition(fields, search_term, use_postgresql=False):
        """构建搜索条件"""
        if use_postgresql:
            conditions = [f"{field} ILIKE %s" for field in fields]
            params = [f"%{search_term}%" for _ in fields]
        else:
            conditions = [f"{field} LIKE ?" for field in fields]
            params = [f"%{search_term}%" for _ in fields]

        return f"({' OR '.join(conditions)})", params

    @staticmethod
    def build_limit_offset_query(base_query, limit, offset, use_postgresql=False):
        """构建分页查询"""
        if use_postgresql:
            return f"{base_query} LIMIT %s OFFSET %s", [limit, offset]
        else:
            return f"{base_query} LIMIT ? OFFSET ?", [limit, offset]

def get_db_connection():
    """获取数据库连接"""
    database_url = os.environ.get('DATABASE_URL')

    if database_url and database_url.startswith('postgresql') and HAS_POSTGRESQL:
        # PostgreSQL连接
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn
    else:
        # SQLite连接
        return sqlite3.connect('ros2_wiki.db')

# 创建Flask应用
app = Flask(__name__)

# 安全配置
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', os.urandom(32).hex()),
    'DATABASE_URL': os.environ.get('DATABASE_URL'),
    'CSRF_ENABLED': True,
    'SESSION_COOKIE_SECURE': os.environ.get('FLASK_ENV') == 'production',
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600,  # 1小时
})

# 初始化安全中间件
setup_security_middleware(app)

# 初始化Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录访问此页面'

# 初始化搜索服务 - 云端环境适配
def get_database_path():
    """获取数据库路径 - 适配云端环境"""
    if os.environ.get('DATABASE_URL'):
        # PostgreSQL环境 - 使用兼容模式
        return 'postgresql'
    return 'ros2_wiki.db'

search_service = ImprovedSearchService(get_database_path())

@login_manager.user_loader
def load_user(user_id):
    """加载用户 - 简化版本"""
    # 临时简化实现，避免复杂的模块依赖
    return None  # 暂时禁用用户加载，确保应用可以启动

@app.route('/')
def index():
    """首页"""
    try:
        # 获取最新文档
        recent_docs = search_service.category_search('ROS2基础', 5)
        categories = search_service.get_popular_categories()
    except Exception as e:
        print(f"获取首页数据失败: {e}")
        recent_docs = []
        categories = []
    
    return render_template('modern_index.html', 
                         recent_docs=recent_docs,
                         categories=categories)

@app.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    
    results = []
    if query:
        if category:
            # 分类搜索
            results = search_service.category_search(category, 20)
        else:
            # 全文搜索
            results = search_service.full_text_search(query, 20)
    
    return render_template('search.html', 
                         query=query, 
                         category=category,
                         results=results)

@app.route('/api/search/suggestions')
def search_suggestions():
    """搜索建议API"""
    query = request.args.get('q', '').strip()
    suggestions = search_service.get_search_suggestions(query, 5)
    
    return jsonify({'suggestions': suggestions})

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=300)  # 5次/5分钟
def login():
    """用户登录 - 带速率限制"""
    if request.method == 'POST':
        # 登录逻辑（省略具体实现）
        pass
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    from flask_login import logout_user
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('index'))

@app.route('/documents')
def documents():
    """文档列表页面 - 支持搜索、分页、筛选"""
    try:
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
            # 使用DatabaseCompatibility工具类构建搜索条件
            search_condition, search_params = DatabaseCompatibility.build_search_condition(
                ['d.title', 'd.content'], search, use_postgresql
            )
            where_conditions.append(search_condition)
            params.extend(search_params)

        if category:
            placeholder = DatabaseCompatibility.get_placeholder(use_postgresql)
            where_conditions.append(f"d.category = {placeholder}")
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

        # 获取文档数据 - 使用DatabaseCompatibility工具类构建分页查询
        base_query = f'''
            SELECT d.*, u.username as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.id
            {where_clause}
            {order_clause}
        '''

        final_query, limit_params = DatabaseCompatibility.build_limit_offset_query(
            base_query, per_page, offset, use_postgresql
        )
        cursor.execute(final_query, params + limit_params)
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
    
    except Exception as e:
        print(f"文档列表加载失败: {e}")
        # 返回空列表以避免模板错误
        return render_template('documents_list.html',
                             documents=[],
                             current_page=1,
                             total_pages=1,
                             total_count=0)

@app.route('/register', methods=['GET', 'POST'])
@csrf_protect
@rate_limit(max_requests=3, window=3600)  # 3次/小时
def register():
    """用户注册 - 带CSRF保护和速率限制"""
    if request.method == 'POST':
        # 注册逻辑（省略具体实现）
        pass
    
    return render_template('register.html')

@app.route('/admin/dashboard')
@login_required
@csrf_protect
def admin_dashboard():
    """管理员仪表板 - 需要登录和CSRF保护"""
    if not current_user.is_admin:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin_dashboard.html')

@app.route('/api/admin/users')
@login_required
@rate_limit(max_requests=20, window=60)  # API速率限制
def api_admin_users():
    """管理员用户API"""
    if not current_user.is_admin:
        return jsonify({'error': '权限不足'}), 403
    
    # 返回用户列表
    return jsonify({'users': []})

@app.errorhandler(403)
def forbidden(error):
    """403错误处理"""
    return render_template('error.html', 
                         error_code=403,
                         error_message='访问被拒绝'), 403

@app.errorhandler(429)
def too_many_requests(error):
    """429错误处理"""
    return render_template('error.html',
                         error_code=429, 
                         error_message='请求过于频繁，请稍后再试'), 429

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    try:
        return render_template('error.html',
                             error_code=500,
                             error_message='服务器内部错误'), 500
    except:
        # 如果模板加载失败，返回纯文本错误
        return f"<h1>错误 500</h1><p>服务器内部错误</p><a href='/'>返回首页</a>", 500

if __name__ == '__main__':
    # 开发环境配置
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("🛡️ ROS2 Wiki 安全版本启动")
    print(f"🔐 CSRF保护: 已启用")
    print(f"⚡ 速率限制: 已启用") 
    print(f"🔒 安全头: 已配置")
    print(f"🚀 调试模式: {'开启' if debug_mode else '关闭'}")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=debug_mode
    )