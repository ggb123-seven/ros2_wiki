"""
数据模型模块
"""

from .user import User
from .document import Document
from .database import get_db_connection, init_db

__all__ = ['User', 'Document', 'get_db_connection', 'init_db']