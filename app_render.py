#!/usr/bin/env python3
"""
ROS2 Wiki - Render部署专用版本
简化版本，确保在Render平台上稳定运行
"""

import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'render-secret-key')

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and 'postgresql' in DATABASE_URL:
    # PostgreSQL配置
    try:
        import psycopg2
        HAS_POSTGRESQL = True
    except ImportError:
        HAS_POSTGRESQL = False
        DATABASE_URL = None
else:
    HAS_POSTGRESQL = False

def get_db_connection():
    """获取数据库连接"""
    if DATABASE_URL and HAS_POSTGRESQL:
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect('ros2_wiki.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_database():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if HAS_POSTGRESQL:
        # PostgreSQL表创建
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(50) DEFAULT 'ROS2基础',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite表创建
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT "ROS2基础",
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """首页"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ROS2 Wiki</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body text-center">
                            <h1 class="card-title text-success">
                                <i class="fas fa-robot"></i> ROS2 Wiki
                            </h1>
                            <p class="card-text">现代化机器人学习平台</p>
                            <p class="text-muted">🎉 部署成功！应用正在Render平台上运行</p>
                            <div class="mt-4">
                                <a href="/health" class="btn btn-primary me-2">
                                    <i class="fas fa-heartbeat"></i> 健康检查
                                </a>
                                <a href="/api/status" class="btn btn-info">
                                    <i class="fas fa-info-circle"></i> 系统状态
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """健康检查"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'platform': 'Render',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/status')
def api_status():
    """API状态"""
    return jsonify({
        'message': 'ROS2 Wiki API is running',
        'status': 'active',
        'database_type': 'PostgreSQL' if HAS_POSTGRESQL else 'SQLite',
        'environment': os.environ.get('FLASK_ENV', 'production')
    })

# 初始化数据库
try:
    init_database()
    print("✅ 数据库初始化成功")
except Exception as e:
    print(f"⚠️ 数据库初始化警告: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
