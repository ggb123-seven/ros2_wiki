"""
用户模型
米醋电子工作室 - SuperClaude重构
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db_connection

class User(UserMixin):
    """用户模型"""
    
    def __init__(self, id, username, email, password_hash, is_admin=False, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = created_at
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    @staticmethod
    def get(user_id):
        """根据ID获取用户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, is_admin, created_at
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        if user_data:
            return User(*user_data)
        return None
    
    @staticmethod
    def get_by_username(username):
        """根据用户名获取用户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, is_admin, created_at
            FROM users WHERE username = ?
        ''', (username,))
        
        user_data = cursor.fetchone()
        if user_data:
            return User(*user_data)
        return None
    
    @staticmethod
    def get_by_email(email):
        """根据邮箱获取用户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, is_admin, created_at
            FROM users WHERE email = ?
        ''', (email,))
        
        user_data = cursor.fetchone()
        if user_data:
            return User(*user_data)
        return None
    
    @staticmethod
    def create(username, email, password, is_admin=False):
        """创建新用户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, is_admin))
            
            conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            conn.rollback()
            raise e
    
    @staticmethod
    def get_all_users(limit=50):
        """获取所有用户列表"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, is_admin, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
    
    def save(self):
        """保存用户更改"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET username = ?, email = ?, password_hash = ?, is_admin = ?
            WHERE id = ?
        ''', (self.username, self.email, self.password_hash, self.is_admin, self.id))
        
        conn.commit()
    
    def delete(self):
        """删除用户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE id = ?', (self.id,))
        conn.commit()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at
        }