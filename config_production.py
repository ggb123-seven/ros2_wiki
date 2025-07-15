#!/usr/bin/env python3
"""
生产环境配置文件
统一本地与云端环境配置
"""

import os
from datetime import timedelta

class ProductionConfig:
    """生产环境配置"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ros2-wiki-production-secret')
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # 数据库配置
    DATABASE_URL = os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///ros2_wiki.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # 应用配置
    APP_NAME = 'ROS2 Wiki'
    VERSION = '2.0.0'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 管理员配置
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@ros2wiki.com')
    
    # 功能开关
    ENABLE_SEARCH = True
    ENABLE_CMS = True
    ENABLE_API = True
    ENABLE_USER_REGISTRATION = True
    
    # API配置
    API_RATE_LIMIT = "100 per hour"
    API_VERSION = "v1"
    
    # 搜索配置
    SEARCH_RESULTS_PER_PAGE = 10
    SEARCH_HIGHLIGHT = True
    
    # 安全头配置
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com fonts.googleapis.com; font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com; img-src 'self' data:;"
    }

class DevelopmentConfig(ProductionConfig):
    """开发环境配置"""
    
    DEBUG = True
    FLASK_ENV = 'development'
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    
    # 开发数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ros2_wiki_dev.db'
    
    # 开发安全头（宽松）
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
    }

class TestingConfig(ProductionConfig):
    """测试环境配置"""
    
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}

def get_config(config_name=None):
    """获取配置"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    return config.get(config_name, config['default'])
