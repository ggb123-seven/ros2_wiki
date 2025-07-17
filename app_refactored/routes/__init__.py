"""
路由模块
"""

from .auth import auth_bp
from .main import main_bp  
from .admin import admin_bp
from .api import api_bp

__all__ = ['auth_bp', 'main_bp', 'admin_bp', 'api_bp']