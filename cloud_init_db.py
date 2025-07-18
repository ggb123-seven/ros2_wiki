#!/usr/bin/env python3
"""
Cloud deployment database initialization
Automatically creates admin account for cloud deployment
"""

import os
import sys
from werkzeug.security import generate_password_hash
from datetime import datetime

def get_db_connection():
    """Get database connection based on environment"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql'):
        # PostgreSQL for cloud deployment
        import psycopg2
        from urllib.parse import urlparse
        
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn, 'postgresql'
    else:
        # SQLite for local development
        import sqlite3
        conn = sqlite3.connect('ros2_wiki.db')
        return conn, 'sqlite'

def create_tables(cursor, db_type):
    """Create database tables"""
    if db_type == 'postgresql':
        # PostgreSQL table creation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blacklisted BOOLEAN DEFAULT FALSE,
                blacklisted_at TIMESTAMP NULL,
                blacklist_reason TEXT NULL,
                last_seen TIMESTAMP NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                author_id INTEGER REFERENCES users(id),
                category VARCHAR(100) DEFAULT 'ROS2基础',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id),
                user_id INTEGER REFERENCES users(id),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id VARCHAR(36) PRIMARY KEY,
                original_name VARCHAR(255) NOT NULL,
                safe_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size BIGINT NOT NULL,
                file_hash VARCHAR(32),
                mime_type VARCHAR(100),
                user_id INTEGER REFERENCES users(id),
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
    else:
        # SQLite table creation (for local development)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blacklisted BOOLEAN DEFAULT 0,
                blacklisted_at TIMESTAMP NULL,
                blacklist_reason TEXT NULL,
                last_seen TIMESTAMP NULL
            )
        ''')
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                original_name TEXT NOT NULL,
                safe_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT,
                mime_type TEXT,
                user_id INTEGER,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

def create_admin_account(cursor, db_type):
    """Create admin account from environment variables"""
    admin_username = os.environ.get('ADMIN_USERNAME', 'ssss')
    admin_email = os.environ.get('ADMIN_EMAIL', 'seventee_0611@qq.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'ssss123')
    
    # Check if admin already exists
    if db_type == 'postgresql':
        cursor.execute('SELECT id FROM users WHERE username = %s OR email = %s', 
                      (admin_username, admin_email))
    else:
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                      (admin_username, admin_email))
    
    if cursor.fetchone():
        print(f"✅ Admin account {admin_username} already exists")
        return
    
    # Create admin account
    password_hash = generate_password_hash(admin_password)
    
    if db_type == 'postgresql':
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted, created_at)
            VALUES (%s, %s, %s, TRUE, FALSE, %s)
        ''', (admin_username, admin_email, password_hash, datetime.now()))
    else:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted, created_at)
            VALUES (?, ?, ?, 1, 0, ?)
        ''', (admin_username, admin_email, password_hash, datetime.now()))
    
    print(f"✅ Created admin account: {admin_username} ({admin_email})")

def create_sample_documents(cursor, db_type):
    """Create sample documents"""
    # Get admin user ID
    if db_type == 'postgresql':
        cursor.execute('SELECT id FROM users WHERE is_admin = TRUE LIMIT 1')
    else:
        cursor.execute('SELECT id FROM users WHERE is_admin = 1 LIMIT 1')
    
    admin_user = cursor.fetchone()
    if not admin_user:
        print("No admin user found, skipping sample documents")
        return
    
    admin_id = admin_user[0]
    
    # Check if documents already exist
    cursor.execute('SELECT COUNT(*) FROM documents')
    doc_count = cursor.fetchone()[0]
    
    if doc_count > 0:
        print(f"✅ Documents already exist ({doc_count} documents)")
        return
    
    sample_docs = [
        {
            'title': 'ROS2入门指南',
            'content': '# ROS2入门指南\n\n这是一个ROS2的入门教程，帮助您快速开始学习ROS2。\n\n## 什么是ROS2？\n\nROS2是一个开源的机器人操作系统框架。',
            'category': 'ROS2基础'
        },
        {
            'title': 'ROS2节点通信',
            'content': '# ROS2节点通信\n\n学习ROS2中节点之间的通信方式。\n\n## 话题通信\n\n话题是ROS2中最常用的通信方式。',
            'category': 'ROS2进阶'
        },
        {
            'title': 'ROS2工作空间',
            'content': '# ROS2工作空间\n\n如何创建和管理ROS2工作空间。\n\n## 创建工作空间\n\n```bash\nmkdir -p ~/ros2_ws/src\n```',
            'category': 'ROS2工具'
        }
    ]
    
    for doc in sample_docs:
        if db_type == 'postgresql':
            cursor.execute('''
                INSERT INTO documents (title, content, author_id, category)
                VALUES (%s, %s, %s, %s)
            ''', (doc['title'], doc['content'], admin_id, doc['category']))
        else:
            cursor.execute('''
                INSERT INTO documents (title, content, author_id, category)
                VALUES (?, ?, ?, ?)
            ''', (doc['title'], doc['content'], admin_id, doc['category']))
    
    print(f"✅ Created {len(sample_docs)} sample documents")

def init_cloud_database():
    """Initialize database for cloud deployment"""
    print("=== Cloud Database Initialization ===")
    
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        print(f"Database type: {db_type}")
        
        # Create tables
        print("Creating database tables...")
        create_tables(cursor, db_type)
        
        # Create admin account if AUTO_CREATE_ADMIN is enabled
        if os.environ.get('AUTO_CREATE_ADMIN', 'false').lower() == 'true':
            print("Creating admin account...")
            create_admin_account(cursor, db_type)
        
        # Create sample documents
        print("Creating sample documents...")
        create_sample_documents(cursor, db_type)
        
        conn.commit()
        conn.close()
        
        print("✅ Cloud database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = init_cloud_database()
    sys.exit(0 if success else 1)
