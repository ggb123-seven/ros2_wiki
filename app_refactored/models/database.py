"""
数据库连接和初始化
米醋电子工作室 - SuperClaude重构
"""

import sqlite3
import os
from flask import current_app, g

def get_db_connection():
    """获取数据库连接"""
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE', 'ros2_wiki.db')
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(error):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
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
            document_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 创建索引（性能优化）
    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title)",
        "CREATE INDEX IF NOT EXISTS idx_documents_author_id ON documents(author_id)",
        "CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)",
        "CREATE INDEX IF NOT EXISTS idx_comments_document_id ON comments(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id)"
    ]
    
    for query in index_queries:
        try:
            cursor.execute(query)
        except sqlite3.Error as e:
            print(f"创建索引失败: {e}")
    
    conn.commit()
    
    # 创建默认管理员
    create_default_admin(cursor, conn)

def create_default_admin(cursor, conn):
    """创建默认管理员账户"""
    from werkzeug.security import generate_password_hash
    
    # 检查是否已存在管理员
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'DevPassword123!@#')
        admin_email = f"{admin_username}@ros2wiki.com"
        
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (admin_username, admin_email, password_hash, True))
        
        conn.commit()
        print(f"默认管理员创建成功: {admin_username}")