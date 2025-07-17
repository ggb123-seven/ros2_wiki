import os
from datetime import timedelta


class Config:
    """基础配置类"""
    # 安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # 会话配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ros2_wiki.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 应用配置
    POSTS_PER_PAGE = 20
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # 日志配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # 开发环境可以不用HTTPS
    
    # 开发环境的默认管理员
    DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'DevPassword123!@#')  # 开发环境强密码


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境密钥（Render会自动生成）
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    
    # 生产环境的管理员设置 - 必须使用环境变量
    DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # 验证生产环境必须配置
    if not DEFAULT_ADMIN_USERNAME or not DEFAULT_ADMIN_PASSWORD:
        raise ValueError("生产环境必须设置ADMIN_USERNAME和ADMIN_PASSWORD环境变量")
    
    # 额外的安全头
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'"
    }


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}