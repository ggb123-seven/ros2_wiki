#!/usr/bin/env python3
"""
优化版本的ROS2 Wiki应用
米醋电子工作室 - SuperClaude全面优化版本
集成缓存、安全、性能、监控等所有优化功能
"""

import os
import sqlite3
import time
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_required, current_user

# 优化模块导入
from optimizations.integration import enhance_flask_app
from optimizations import (
    DocumentCache, 
    SearchCache, 
    cache_result, 
    require_security_check,
    security_manager,
    audit_log
)

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

def is_postgresql():
    """判断是否使用PostgreSQL"""
    database_url = os.environ.get('DATABASE_URL')
    return database_url and database_url.startswith('postgresql') and HAS_POSTGRESQL

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

# 应用优化模块
enhance_flask_app(app)

# 初始化Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录访问此页面'

# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
        cursor.execute(f"SELECT * FROM users WHERE id = {placeholder}", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            from werkzeug.security import UserMixin
            
            class User(UserMixin):
                def __init__(self, id, username, email, is_admin=False):
                    self.id = id
                    self.username = username
                    self.email = email
                    self.is_admin = is_admin
            
            return User(user_data[0], user_data[1], user_data[2], bool(user_data[4]))
        return None
    except Exception as e:
        print(f"加载用户失败: {e}")
        return None

# 路由定义
@app.route('/')
@cache_result('homepage', ttl=300)  # 缓存5分钟
def index():
    """首页 - 带缓存优化"""
    try:
        # 使用缓存的文档获取
        recent_documents = DocumentCache.get_document_list(limit=6)
        popular_categories = DocumentCache.get_popular_categories()
        
        # 统计信息
        stats = get_site_stats()
        
        return render_template('index.html', 
                             documents=recent_documents,
                             categories=popular_categories,
                             stats=stats)
    except Exception as e:
        print(f"首页加载失败: {e}")
        return render_template('index.html', 
                             documents=[], 
                             categories=[], 
                             stats={})

@app.route('/documents')
def documents():
    """文档列表页面 - 移除登录要求并优化"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 10
        category = request.args.get('category')
        
        # 使用缓存的文档获取
        documents = DocumentCache.get_document_list(category=category, limit=per_page)
        
        return render_template('documents.html', 
                             documents=documents, 
                             page=page,
                             category=category)
    except Exception as e:
        print(f"文档列表加载失败: {e}")
        return render_template('documents.html', documents=[], page=1)

@app.route('/documents/<int:doc_id>')
@cache_result('document_detail', ttl=1800)  # 缓存30分钟
def document_detail(doc_id):
    """文档详情页面 - 带缓存优化"""
    try:
        # 使用缓存的文档获取
        document = DocumentCache.get_document_detail(doc_id)
        
        if not document:
            flash('文档不存在', 'error')
            return redirect(url_for('documents'))
        
        return render_template('document_detail.html', document=document)
    except Exception as e:
        print(f"文档详情加载失败: {e}")
        flash('文档加载失败', 'error')
        return redirect(url_for('documents'))

@app.route('/search')
def search():
    """搜索页面 - 带缓存优化"""
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    
    if not query:
        return render_template('search.html', results=[], query='', page=page)
    
    try:
        # 使用缓存的搜索
        results = SearchCache.search_documents(query, limit=20)
        
        # 记录搜索事件
        audit_log.log_event('search_query', {
            'query': query,
            'results_count': len(results),
            'page': page
        })
        
        return render_template('search.html', 
                             results=results, 
                             query=query, 
                             page=page)
    except Exception as e:
        print(f"搜索失败: {e}")
        return render_template('search.html', results=[], query=query, page=page)

@app.route('/login', methods=['GET', 'POST'])
@require_security_check
def login():
    """登录页面 - 带安全检查"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('login.html')
        
        try:
            # 记录登录尝试
            client_ip = security_manager.get_client_ip()
            
            # 验证用户
            user = authenticate_user(username, password)
            
            if user:
                # 登录成功
                from flask_login import login_user
                login_user(user)
                
                # 记录成功登录
                audit_log.log_login_attempt(username, True, client_ip)
                
                flash('登录成功', 'success')
                return redirect(url_for('index'))
            else:
                # 登录失败
                security_manager.record_failed_attempt(client_ip)
                audit_log.log_login_attempt(username, False, client_ip)
                
                flash('用户名或密码错误', 'error')
        except Exception as e:
            print(f"登录过程失败: {e}")
            flash('登录失败，请稍后重试', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """登出"""
    from flask_login import logout_user
    
    # 记录登出事件
    audit_log.log_event('logout', {
        'user_id': current_user.id,
        'username': current_user.username
    })
    
    logout_user()
    flash('已成功登出', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """管理员仪表板"""
    if not current_user.is_admin:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    try:
        # 获取系统统计
        stats = get_admin_stats()
        
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        print(f"管理员仪表板加载失败: {e}")
        return render_template('admin/dashboard.html', stats={})

@app.route('/admin/cache')
@login_required
def admin_cache():
    """缓存管理"""
    if not current_user.is_admin:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    from optimizations.cache_manager import CacheStats
    
    try:
        cache_health = CacheStats.get_cache_health()
        return render_template('admin/cache.html', cache_health=cache_health)
    except Exception as e:
        print(f"缓存管理页面加载失败: {e}")
        return render_template('admin/cache.html', cache_health={})

@app.route('/admin/security')
@login_required
def admin_security():
    """安全管理"""
    if not current_user.is_admin:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    try:
        security_stats = {
            'blocked_ips': list(security_manager.blocked_ips),
            'failed_attempts': len(security_manager.failed_attempts),
            'threat_scores': len(security_manager.threat_detector.threat_scores)
        }
        
        return render_template('admin/security.html', security_stats=security_stats)
    except Exception as e:
        print(f"安全管理页面加载失败: {e}")
        return render_template('admin/security.html', security_stats={})

# 辅助函数
def authenticate_user(username, password):
    """验证用户"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
        cursor.execute(f"SELECT * FROM users WHERE username = {placeholder}", (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            from werkzeug.security import check_password_hash, UserMixin
            
            if check_password_hash(user_data[3], password):
                class User(UserMixin):
                    def __init__(self, id, username, email, is_admin=False):
                        self.id = id
                        self.username = username
                        self.email = email
                        self.is_admin = is_admin
                
                return User(user_data[0], user_data[1], user_data[2], bool(user_data[4]))
        
        return None
    except Exception as e:
        print(f"用户验证失败: {e}")
        return None

@cache_result('site_stats', ttl=600)  # 缓存10分钟
def get_site_stats():
    """获取网站统计信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 文档数量
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        # 用户数量
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # 分类数量
        cursor.execute("SELECT COUNT(DISTINCT category) FROM documents")
        category_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'documents': doc_count,
            'users': user_count,
            'categories': category_count
        }
    except Exception as e:
        print(f"获取统计信息失败: {e}")
        return {'documents': 0, 'users': 0, 'categories': 0}

def get_admin_stats():
    """获取管理员统计信息"""
    try:
        from optimizations.cache_manager import CacheStats
        
        basic_stats = get_site_stats()
        cache_health = CacheStats.get_cache_health()
        
        # 安全统计
        security_stats = {
            'blocked_ips': len(security_manager.blocked_ips),
            'failed_attempts': len(security_manager.failed_attempts),
            'rate_limited_ips': len(security_manager.rate_limits)
        }
        
        return {
            'basic': basic_stats,
            'cache': cache_health,
            'security': security_stats
        }
    except Exception as e:
        print(f"获取管理员统计失败: {e}")
        return {}

# 错误处理
@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    """403错误处理"""
    return render_template('errors/403.html'), 403

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """429错误处理 - 速率限制"""
    return render_template('errors/429.html'), 429

if __name__ == '__main__':
    # 开发模式
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))