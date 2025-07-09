from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    from config import config
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 配置登录管理
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册上下文处理器
    register_context_processors(app)
    
    # 配置日志
    configure_logging(app)
    
    # 安全头中间件
    configure_security_headers(app)
    
    # 初始化数据库
    with app.app_context():
        init_database()
    
    return app


def register_blueprints(app):
    """注册所有蓝图"""
    # 主要页面蓝图
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # 认证蓝图
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 原有管理蓝图
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # 新增功能蓝图
    try:
        # 搜索功能蓝图
        from app.search import search_bp
        app.register_blueprint(search_bp, url_prefix='/search')
        
        # CMS管理蓝图
        from app.cms import cms_bp
        app.register_blueprint(cms_bp, url_prefix='/admin/cms')
        
        # 用户权限管理蓝图
        from app.permissions import permissions_bp
        app.register_blueprint(permissions_bp, url_prefix='/admin/users')
        
        # API蓝图
        from app.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        
    except ImportError as e:
        app.logger.warning(f'部分蓝图导入失败: {e}')


def register_error_handlers(app):
    """注册错误处理器"""
    try:
        from app.errors import errors_bp
        app.register_blueprint(errors_bp)
    except ImportError:
        # 如果错误处理蓝图不存在，注册基本错误处理
        register_basic_error_handlers(app)


def register_basic_error_handlers(app):
    """注册基本错误处理器"""
    from flask import render_template, jsonify, request
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': '资源不存在'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': '服务器内部错误'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': '访问被禁止'}), 403
        return render_template('errors/403.html'), 403


def register_context_processors(app):
    """注册上下文处理器"""
    @app.context_processor
    def inject_app_info():
        """在所有模板中注入应用信息"""
        return {
            'app_name': app.config.get('APP_NAME', 'ROS2 Wiki'),
            'version': app.config.get('VERSION', '2.0.0')
        }
    
    @app.context_processor
    def inject_user_counts():
        """注入统计信息"""
        try:
            from app.models import get_user_count, get_document_count
            return {
                'user_count': get_user_count(),
                'document_count': get_document_count()
            }
        except Exception:
            return {'user_count': 0, 'document_count': 0}


def configure_logging(app):
    """配置日志系统"""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/ros2_wiki.log',
                                         maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('ROS2 Wiki startup')


def configure_security_headers(app):
    """配置安全头"""
    if app.config.get('SECURITY_HEADERS'):
        @app.after_request
        def set_security_headers(response):
            for header, value in app.config['SECURITY_HEADERS'].items():
                response.headers[header] = value
            return response


def init_database():
    """初始化数据库"""
    try:
        # 尝试使用新的模型系统
        from app.models import init_db
        init_db()
    except ImportError:
        # 回退到原有的初始化方式
        init_legacy_database()


def init_legacy_database():
    """兼容原有数据库初始化"""
    import sqlite3
    from flask import current_app
    
    db_path = current_app.config.get('SQLITE_DATABASE_URL', 'sqlite:///ros2_wiki.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]
    
    conn = sqlite3.connect(db_path)
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


# Flask-Login用户加载器
@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    try:
        from app.models import User
        return User.get(user_id)
    except ImportError:
        # 回退到原有的用户加载方式
        return load_legacy_user(user_id)


def load_legacy_user(user_id):
    """兼容原有用户加载"""
    import sqlite3
    from flask import current_app
    from flask_login import UserMixin
    
    class LegacyUser(UserMixin):
        def __init__(self, id, username, email, is_admin=False):
            self.id = id
            self.username = username
            self.email = email
            self.is_admin = is_admin
    
    db_path = current_app.config.get('SQLITE_DATABASE_URL', 'sqlite:///ros2_wiki.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return LegacyUser(user[0], user[1], user[2], user[4] if len(user) > 4 else False)
        return None
    except Exception:
        return None