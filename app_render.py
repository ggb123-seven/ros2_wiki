#!/usr/bin/env python3
"""
Render平台优化版本的ROS2 Wiki应用
米醋电子工作室 - 适配Render云部署
"""

import os
import sqlite3
import logging
import hashlib
import uuid
import mimetypes
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_required, current_user, login_user, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL支持
try:
    import psycopg2
    import psycopg2.extras
    HAS_POSTGRESQL = True
    logger.info("✅ PostgreSQL支持已启用")
except ImportError:
    HAS_POSTGRESQL = False
    logger.warning("⚠️ PostgreSQL不可用，使用SQLite")

# 简化的缓存系统（内存缓存）
class SimpleCache:
    """简化的内存缓存系统"""
    
    def __init__(self):
        self._cache = {}
        self._max_size = 1000  # 最大缓存项数
    
    def get(self, key):
        """获取缓存"""
        return self._cache.get(key)
    
    def set(self, key, value, ttl=3600):
        """设置缓存"""
        if len(self._cache) >= self._max_size:
            # 简单的LRU清理
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = value
        return True
    
    def delete(self, key):
        """删除缓存"""
        return self._cache.pop(key, None) is not None
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        return True

# 全局缓存实例
cache = SimpleCache()

# 文件管理系统
class FileManager:
    """文件管理系统 - 适配Render平台"""
    
    def __init__(self):
        self.upload_folder = '/tmp/uploads'  # Render临时目录
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
            'xls', 'xlsx', 'ppt', 'pptx', 'md', 'zip', 'rar'
        }
        self.ensure_upload_folder()
    
    def ensure_upload_folder(self):
        """确保上传文件夹存在"""
        try:
            os.makedirs(self.upload_folder, exist_ok=True)
        except Exception as e:
            logger.error(f"创建上传目录失败: {e}")
    
    def allowed_file(self, filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def get_file_hash(self, file_path):
        """获取文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"获取文件哈希失败: {e}")
            return None
    
    def save_file(self, file, user_id):
        """保存文件并返回文件信息"""
        try:
            if not file or not file.filename:
                return None, "没有选择文件"
            
            if not self.allowed_file(file.filename):
                return None, "不支持的文件类型"
            
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            file_extension = filename.rsplit('.', 1)[1].lower()
            safe_filename = f"{file_id}.{file_extension}"
            
            # 保存文件
            file_path = os.path.join(self.upload_folder, safe_filename)
            file.save(file_path)
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            file_hash = self.get_file_hash(file_path)
            mime_type = mimetypes.guess_type(filename)[0]
            
            # 检查文件大小
            if file_size > self.max_file_size:
                os.remove(file_path)
                return None, f"文件大小超过限制 ({self.max_file_size // 1024 // 1024}MB)"
            
            # 保存到数据库
            file_info = {
                'id': file_id,
                'original_name': filename,
                'safe_filename': safe_filename,
                'file_path': file_path,
                'file_size': file_size,
                'file_hash': file_hash,
                'mime_type': mime_type,
                'user_id': user_id,
                'upload_time': datetime.now()
            }
            
            if self.save_file_to_db(file_info):
                return file_info, "文件上传成功"
            else:
                os.remove(file_path)
                return None, "数据库保存失败"
                
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            return None, f"文件保存失败: {str(e)}"
    
    def save_file_to_db(self, file_info):
        """将文件信息保存到数据库"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
            
            cursor.execute(f"""
                INSERT INTO files (id, original_name, safe_filename, file_path, 
                                 file_size, file_hash, mime_type, user_id, upload_time)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                        {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (
                file_info['id'], file_info['original_name'], file_info['safe_filename'],
                file_info['file_path'], file_info['file_size'], file_info['file_hash'],
                file_info['mime_type'], file_info['user_id'], file_info['upload_time']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"文件信息保存失败: {e}")
            return False
    
    def get_file_info(self, file_id):
        """获取文件信息"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
            cursor.execute(f"""
                SELECT f.*, u.username as uploader_name
                FROM files f
                LEFT JOIN users u ON f.user_id = u.id
                WHERE f.id = {placeholder}
            """, (file_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'original_name': row[1],
                    'safe_filename': row[2],
                    'file_path': row[3],
                    'file_size': row[4],
                    'file_hash': row[5],
                    'mime_type': row[6],
                    'user_id': row[7],
                    'upload_time': str(row[8]),
                    'uploader_name': row[9] if len(row) > 9 else 'Unknown'
                }
            return None
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None
    
    def get_user_files(self, user_id, limit=50):
        """获取用户的文件列表"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
            cursor.execute(f"""
                SELECT id, original_name, file_size, mime_type, upload_time
                FROM files
                WHERE user_id = {placeholder}
                ORDER BY upload_time DESC
                LIMIT {placeholder}
            """, (user_id, limit))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'id': row[0],
                    'original_name': row[1],
                    'file_size': row[2],
                    'mime_type': row[3],
                    'upload_time': str(row[4])
                })
            
            conn.close()
            return files
            
        except Exception as e:
            logger.error(f"获取用户文件列表失败: {e}")
            return []
    
    def delete_file(self, file_id, user_id):
        """删除文件"""
        try:
            file_info = self.get_file_info(file_id)
            if not file_info:
                return False, "文件不存在"
            
            # 检查权限
            if file_info['user_id'] != user_id:
                return False, "没有权限删除此文件"
            
            # 删除物理文件
            if os.path.exists(file_info['file_path']):
                os.remove(file_info['file_path'])
            
            # 删除数据库记录
            conn = get_db_connection()
            cursor = conn.cursor()
            
            placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
            cursor.execute(f"DELETE FROM files WHERE id = {placeholder}", (file_id,))
            
            conn.commit()
            conn.close()
            
            return True, "文件删除成功"
            
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False, f"删除文件失败: {str(e)}"
    
    def format_file_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

# 全局文件管理器实例
file_manager = FileManager()

# 模板过滤器
@app.template_filter('format_file_size')
def format_file_size(size):
    """格式化文件大小的模板过滤器"""
    return file_manager.format_file_size(size)

# 数据库兼容性工具类
class DatabaseCompatibility:
    """数据库兼容性工具类"""

    @staticmethod
    def get_placeholder(use_postgresql=False):
        return '%s' if use_postgresql else '?'

    @staticmethod
    def build_search_condition(fields, search_term, use_postgresql=False):
        if use_postgresql:
            conditions = [f"{field} ILIKE %s" for field in fields]
            params = [f"%{search_term}%" for _ in fields]
        else:
            conditions = [f"{field} LIKE ?" for field in fields]
            params = [f"%{search_term}%" for _ in fields]
        return f"({' OR '.join(conditions)})", params

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

# 用户类
class User(UserMixin):
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

# 创建Flask应用
app = Flask(__name__)

# 基础配置
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'render-secret-key-change-in-production'),
    'DATABASE_URL': os.environ.get('DATABASE_URL'),
    'SESSION_COOKIE_SECURE': os.environ.get('RENDER') == 'true',
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,  # 10MB文件大小限制
    'UPLOAD_FOLDER': '/tmp/uploads',  # 上传目录
})

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
            return User(user_data[0], user_data[1], user_data[2], bool(user_data[4]))
        return None
    except Exception as e:
        logger.error(f"加载用户失败: {e}")
        return None

# 缓存装饰器
def cache_result(key_prefix, ttl=3600):
    """简化的缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{':'.join(map(str, args))}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# 路由定义
@app.route('/')
@cache_result('homepage', ttl=300)
def index():
    """首页"""
    try:
        # 获取最新文档
        recent_documents = get_recent_documents(6)
        
        # 获取统计信息
        stats = get_site_stats()
        
        return render_template('index.html', 
                             documents=recent_documents,
                             stats=stats)
    except Exception as e:
        logger.error(f"首页加载失败: {e}")
        return render_template('index.html', documents=[], stats={})

@app.route('/documents')
def documents():
    """文档列表页面"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 10
        category = request.args.get('category')
        
        documents = get_documents(category=category, limit=per_page, page=page)
        
        return render_template('documents.html', 
                             documents=documents, 
                             page=page,
                             category=category)
    except Exception as e:
        logger.error(f"文档列表加载失败: {e}")
        return render_template('documents.html', documents=[], page=1)

@app.route('/documents/<int:doc_id>')
@cache_result('document_detail', ttl=1800)
def document_detail(doc_id):
    """文档详情页面"""
    try:
        document = get_document_by_id(doc_id)
        
        if not document:
            flash('文档不存在', 'error')
            return redirect(url_for('documents'))
        
        return render_template('document_detail.html', document=document)
    except Exception as e:
        logger.error(f"文档详情加载失败: {e}")
        flash('文档加载失败', 'error')
        return redirect(url_for('documents'))

@app.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search.html', results=[], query='')
    
    try:
        results = search_documents(query)
        return render_template('search.html', results=results, query=query)
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return render_template('search.html', results=[], query=query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('login.html')
        
        try:
            user = authenticate_user(username, password)
            
            if user:
                login_user(user)
                flash('登录成功', 'success')
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误', 'error')
        except Exception as e:
            logger.error(f"登录失败: {e}")
            flash('登录失败，请稍后重试', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """登出"""
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
        stats = get_admin_stats()
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"管理员仪表板加载失败: {e}")
        return render_template('admin/dashboard.html', stats={})

# API路由
@app.route('/api/search/suggestions')
def search_suggestions():
    """搜索建议API"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'suggestions': []})
    
    try:
        suggestions = get_search_suggestions(query)
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        logger.error(f"搜索建议失败: {e}")
        return jsonify({'suggestions': []})

# 文件相关路由
@app.route('/files')
@login_required
def files():
    """文件管理页面"""
    try:
        user_files = file_manager.get_user_files(current_user.id)
        return render_template('files.html', files=user_files)
    except Exception as e:
        logger.error(f"文件管理页面加载失败: {e}")
        return render_template('files.html', files=[])

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """文件上传"""
    try:
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.referrer or url_for('files'))
        
        file = request.files['file']
        file_info, message = file_manager.save_file(file, current_user.id)
        
        if file_info:
            flash(f'文件上传成功: {file_info["original_name"]}', 'success')
        else:
            flash(f'文件上传失败: {message}', 'error')
        
        return redirect(request.referrer or url_for('files'))
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        flash('文件上传失败', 'error')
        return redirect(request.referrer or url_for('files'))

@app.route('/download/<file_id>')
@login_required
def download_file(file_id):
    """文件下载"""
    try:
        file_info = file_manager.get_file_info(file_id)
        if not file_info:
            flash('文件不存在', 'error')
            return redirect(url_for('files'))
        
        # 检查文件是否存在
        if not os.path.exists(file_info['file_path']):
            flash('文件已被删除', 'error')
            return redirect(url_for('files'))
        
        return send_file(
            file_info['file_path'],
            as_attachment=True,
            download_name=file_info['original_name']
        )
        
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        flash('文件下载失败', 'error')
        return redirect(url_for('files'))

@app.route('/delete_file/<file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """删除文件"""
    try:
        success, message = file_manager.delete_file(file_id, current_user.id)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('files'))
        
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        flash('删除文件失败', 'error')
        return redirect(url_for('files'))

@app.route('/file_info/<file_id>')
@login_required
def file_info(file_id):
    """获取文件信息"""
    try:
        file_info = file_manager.get_file_info(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 格式化文件大小
        file_info['formatted_size'] = file_manager.format_file_size(file_info['file_size'])
        
        return jsonify(file_info)
        
    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        return jsonify({'error': '获取文件信息失败'}), 500

@app.route('/api/health')
def health_check():
    """健康检查"""
    try:
        # 数据库连接测试
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'active',
            'timestamp': os.environ.get('RENDER_SERVICE_ID', 'local')
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

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
        
        if user_data and check_password_hash(user_data[3], password):
            return User(user_data[0], user_data[1], user_data[2], bool(user_data[4]))
        
        return None
    except Exception as e:
        logger.error(f"用户验证失败: {e}")
        return None

def get_recent_documents(limit=10):
    """获取最新文档"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
        cursor.execute(f"""
            SELECT id, title, content, category, created_at
            FROM documents
            ORDER BY created_at DESC
            LIMIT {placeholder}
        """, (limit,))
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'id': row[0],
                'title': row[1],
                'content': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                'category': row[3],
                'created_at': str(row[4])
            })
        
        conn.close()
        return documents
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        return []

def get_documents(category=None, limit=10, page=1):
    """获取文档列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
        offset = (page - 1) * limit
        
        if category:
            cursor.execute(f"""
                SELECT id, title, content, category, created_at
                FROM documents
                WHERE category = {placeholder}
                ORDER BY created_at DESC
                LIMIT {placeholder} OFFSET {placeholder}
            """, (category, limit, offset))
        else:
            cursor.execute(f"""
                SELECT id, title, content, category, created_at
                FROM documents
                ORDER BY created_at DESC
                LIMIT {placeholder} OFFSET {placeholder}
            """, (limit, offset))
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'id': row[0],
                'title': row[1],
                'content': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                'category': row[3],
                'created_at': str(row[4])
            })
        
        conn.close()
        return documents
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return []

def get_document_by_id(doc_id):
    """根据ID获取文档"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
        cursor.execute(f"""
            SELECT d.*, u.username as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.id = {placeholder}
        """, (doc_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'author_id': row[3],
                'category': row[4],
                'created_at': str(row[5]),
                'updated_at': str(row[6]),
                'author_name': row[7] if len(row) > 7 else 'Unknown'
            }
        return None
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}")
        return None

def search_documents(query, limit=20):
    """搜索文档"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_condition, params = DatabaseCompatibility.build_search_condition(
            ['title', 'content', 'category'], query, is_postgresql()
        )
        
        placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
        cursor.execute(f"""
            SELECT id, title, content, category, created_at
            FROM documents
            WHERE {search_condition}
            ORDER BY created_at DESC
            LIMIT {placeholder}
        """, params + [limit])
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'content': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                'category': row[3],
                'created_at': str(row[4])
            })
        
        conn.close()
        return results
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return []

def get_search_suggestions(query, limit=5):
    """获取搜索建议"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = DatabaseCompatibility.get_placeholder(is_postgresql())
        
        if is_postgresql():
            cursor.execute("""
                SELECT DISTINCT title
                FROM documents
                WHERE title ILIKE %s
                ORDER BY title
                LIMIT %s
            """, (f"%{query}%", limit))
        else:
            cursor.execute("""
                SELECT DISTINCT title
                FROM documents
                WHERE title LIKE ?
                ORDER BY title
                LIMIT ?
            """, (f"%{query}%", limit))
        
        suggestions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return suggestions
    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        return []

@cache_result('site_stats', ttl=600)
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
        logger.error(f"获取统计信息失败: {e}")
        return {'documents': 0, 'users': 0, 'categories': 0}

def get_admin_stats():
    """获取管理员统计信息"""
    try:
        basic_stats = get_site_stats()
        
        return {
            'basic': basic_stats,
            'cache': {
                'type': 'memory',
                'size': len(cache._cache)
            },
            'system': {
                'database': 'postgresql' if is_postgresql() else 'sqlite',
                'environment': 'render' if os.environ.get('RENDER') else 'local'
            }
        }
    except Exception as e:
        logger.error(f"获取管理员统计失败: {e}")
        return {}

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)