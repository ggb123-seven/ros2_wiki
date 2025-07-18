#!/usr/bin/env python3
"""
优化配置文件
米醋电子工作室 - 统一管理所有优化配置
"""

import os
from datetime import timedelta

class OptimizationConfig:
    """优化配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # 安全配置
    SECURITY_CONFIG = {
        'MAX_FAILED_ATTEMPTS': 5,
        'LOCKOUT_DURATION': timedelta(minutes=30),
        'RATE_LIMIT_WINDOW': timedelta(minutes=1),
        'MAX_REQUESTS_PER_MINUTE': 60,
        'ENABLE_CSRF': True,
        'SECURE_COOKIES': os.environ.get('FLASK_ENV') == 'production',
        'SESSION_TIMEOUT': timedelta(hours=24),
        'REQUIRE_HTTPS': os.environ.get('FLASK_ENV') == 'production'
    }
    
    # 缓存配置
    CACHE_CONFIG = {
        'REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
        'DEFAULT_TTL': 3600,  # 1小时
        'CACHE_PREFIX': 'ros2_wiki:',
        'ENABLE_MEMORY_FALLBACK': True,
        'CACHE_COMPRESSION': True,
        'MAX_MEMORY_CACHE_SIZE': 100 * 1024 * 1024  # 100MB
    }
    
    # 搜索配置
    SEARCH_CONFIG = {
        'ENABLE_FULL_TEXT_SEARCH': True,
        'SEARCH_RESULTS_PER_PAGE': 20,
        'SEARCH_SUGGESTIONS_LIMIT': 5,
        'SEARCH_CACHE_TTL': 900,  # 15分钟
        'ENABLE_SEARCH_ANALYTICS': True
    }
    
    # 性能配置
    PERFORMANCE_CONFIG = {
        'ENABLE_COMPRESSION': True,
        'ENABLE_ETAG': True,
        'STATIC_FILES_CACHE_TIMEOUT': 86400,  # 24小时
        'ENABLE_LAZY_LOADING': True,
        'ENABLE_CDN': os.environ.get('FLASK_ENV') == 'production',
        'CDN_DOMAIN': os.environ.get('CDN_DOMAIN', '')
    }
    
    # 监控配置
    MONITORING_CONFIG = {
        'ENABLE_METRICS': True,
        'METRICS_INTERVAL': 60,  # 秒
        'ENABLE_HEALTH_CHECK': True,
        'HEALTH_CHECK_ENDPOINT': '/api/monitoring/health',
        'ENABLE_PERFORMANCE_TRACKING': True,
        'LOG_LEVEL': 'INFO' if not DEBUG else 'DEBUG'
    }
    
    # OAuth配置
    OAUTH_CONFIG = {
        'GITHUB_CLIENT_ID': os.environ.get('GITHUB_CLIENT_ID'),
        'GITHUB_CLIENT_SECRET': os.environ.get('GITHUB_CLIENT_SECRET'),
        'GOOGLE_CLIENT_ID': os.environ.get('GOOGLE_CLIENT_ID'),
        'GOOGLE_CLIENT_SECRET': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'ENABLE_OAUTH_LOGIN': True,
        'OAUTH_CALLBACK_URL': os.environ.get('OAUTH_CALLBACK_URL', 'http://localhost:5000')
    }
    
    # 文档配置
    DOCUMENT_CONFIG = {
        'DOCUMENTS_PER_PAGE': 10,
        'ENABLE_DOCUMENT_VERSIONING': True,
        'ENABLE_DOCUMENT_COMMENTS': True,
        'ENABLE_DOCUMENT_RATING': True,
        'DOCUMENT_UPLOAD_MAX_SIZE': 10 * 1024 * 1024,  # 10MB
        'ALLOWED_FILE_EXTENSIONS': ['.md', '.txt', '.pdf', '.doc', '.docx']
    }
    
    # 前端配置
    FRONTEND_CONFIG = {
        'ENABLE_PWA': True,
        'ENABLE_DARK_MODE': True,
        'ENABLE_RESPONSIVE_IMAGES': True,
        'ENABLE_INFINITE_SCROLL': True,
        'ENABLE_OFFLINE_MODE': True,
        'THEME_COLORS': {
            'primary': '#007bff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'info': '#17a2b8',
            'warning': '#ffc107',
            'danger': '#dc3545'
        }
    }
    
    # 数据库配置
    DATABASE_CONFIG = {
        'ENABLE_CONNECTION_POOLING': True,
        'MAX_CONNECTIONS': 20,
        'CONNECTION_TIMEOUT': 30,
        'ENABLE_QUERY_LOGGING': DEBUG,
        'ENABLE_SLOW_QUERY_LOG': True,
        'SLOW_QUERY_THRESHOLD': 1.0  # 秒
    }
    
    # 邮件配置
    EMAIL_CONFIG = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': True,
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER')
    }
    
    # 日志配置
    LOGGING_CONFIG = {
        'LOG_LEVEL': 'INFO' if not DEBUG else 'DEBUG',
        'LOG_FILE': 'logs/ros2_wiki.log',
        'LOG_MAX_SIZE': 10 * 1024 * 1024,  # 10MB
        'LOG_BACKUP_COUNT': 10,
        'ENABLE_CONSOLE_LOG': DEBUG,
        'ENABLE_FILE_LOG': True,
        'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
    
    @classmethod
    def get_config_dict(cls):
        """获取配置字典"""
        return {
            'SECRET_KEY': cls.SECRET_KEY,
            'DATABASE_URL': cls.DATABASE_URL,
            'DEBUG': cls.DEBUG,
            'SECURITY': cls.SECURITY_CONFIG,
            'CACHE': cls.CACHE_CONFIG,
            'SEARCH': cls.SEARCH_CONFIG,
            'PERFORMANCE': cls.PERFORMANCE_CONFIG,
            'MONITORING': cls.MONITORING_CONFIG,
            'OAUTH': cls.OAUTH_CONFIG,
            'DOCUMENT': cls.DOCUMENT_CONFIG,
            'FRONTEND': cls.FRONTEND_CONFIG,
            'DATABASE': cls.DATABASE_CONFIG,
            'EMAIL': cls.EMAIL_CONFIG,
            'LOGGING': cls.LOGGING_CONFIG
        }
    
    @classmethod
    def validate_config(cls):
        """验证配置完整性"""
        issues = []
        
        # 检查必要配置
        if not cls.SECRET_KEY:
            issues.append("SECRET_KEY未设置")
        
        if not cls.DATABASE_URL and not os.path.exists('ros2_wiki.db'):
            issues.append("未配置数据库连接")
        
        # 检查OAuth配置
        if cls.OAUTH_CONFIG['ENABLE_OAUTH_LOGIN']:
            if not cls.OAUTH_CONFIG['GITHUB_CLIENT_ID'] and not cls.OAUTH_CONFIG['GOOGLE_CLIENT_ID']:
                issues.append("OAuth已启用但未配置客户端ID")
        
        # 检查邮件配置
        if cls.EMAIL_CONFIG['MAIL_USERNAME'] and not cls.EMAIL_CONFIG['MAIL_PASSWORD']:
            issues.append("邮件用户名已设置但缺少密码")
        
        # 检查日志目录
        log_dir = os.path.dirname(cls.LOGGING_CONFIG['LOG_FILE'])
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError:
                issues.append(f"无法创建日志目录: {log_dir}")
        
        return issues
    
    @classmethod
    def get_flask_config(cls):
        """获取Flask配置"""
        return {
            'SECRET_KEY': cls.SECRET_KEY,
            'DATABASE_URL': cls.DATABASE_URL,
            'DEBUG': cls.DEBUG,
            'CSRF_ENABLED': cls.SECURITY_CONFIG['ENABLE_CSRF'],
            'SESSION_COOKIE_SECURE': cls.SECURITY_CONFIG['SECURE_COOKIES'],
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': cls.SECURITY_CONFIG['SESSION_TIMEOUT'],
            'SEND_FILE_MAX_AGE_DEFAULT': cls.PERFORMANCE_CONFIG['STATIC_FILES_CACHE_TIMEOUT'],
            'COMPRESS_MIMETYPES': [
                'text/html', 'text/css', 'text/xml', 'text/javascript',
                'application/javascript', 'application/json'
            ] if cls.PERFORMANCE_CONFIG['ENABLE_COMPRESSION'] else []
        }

# 导出配置实例
config = OptimizationConfig()

# 验证配置
config_issues = config.validate_config()
if config_issues:
    print("⚠️ 配置验证发现问题:")
    for issue in config_issues:
        print(f"  - {issue}")
else:
    print("✅ 配置验证通过")

if __name__ == "__main__":
    # 配置测试
    print("🔧 优化配置测试")
    print("=" * 50)
    
    config_dict = OptimizationConfig.get_config_dict()
    
    for section, settings in config_dict.items():
        print(f"\n📋 {section}配置:")
        if isinstance(settings, dict):
            for key, value in settings.items():
                # 隐藏敏感信息
                if 'SECRET' in key or 'PASSWORD' in key or 'TOKEN' in key:
                    value = "***已隐藏***" if value else "未设置"
                print(f"  {key}: {value}")
        else:
            print(f"  值: {settings}")
    
    print("\n" + "=" * 50)
    print("配置测试完成")