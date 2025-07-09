#!/usr/bin/env python3
"""
PostgreSQL数据库初始化脚本
用于创建新的PostgreSQL数据库结构
"""
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# 创建Flask应用
app = Flask(__name__)

# 从环境变量或默认值获取数据库URL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres123@localhost:5432/ros2_wiki')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_database():
    """初始化数据库"""
    print(f"连接到数据库: {DATABASE_URL}")
    
    try:
        # 创建所有表
        with app.app_context():
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 创建默认管理员账号
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@ros2wiki.local',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ 默认管理员账号创建成功: admin / admin123")
                print("⚠️  请在生产环境中立即修改默认密码！")
            else:
                print("ℹ️  管理员账号已存在")
            
            # 创建示例文档
            if Document.query.count() == 0:
                sample_doc = Document(
                    title='欢迎使用ROS2 Wiki',
                    content='''# 欢迎使用ROS2 Wiki

这是一个基于Flask的ROS2文档管理系统。

## 主要功能

- 📝 Markdown文档编写
- 🔍 全文搜索（PostgreSQL）
- 👥 用户管理
- 💬 评论系统
- 🔐 权限控制

## 快速开始

1. 使用管理员账号登录
2. 创建新的文档
3. 使用Markdown语法编写内容
4. 发布并分享

## 技术特性

- **数据库**: PostgreSQL with 全文搜索
- **后端**: Flask + SQLAlchemy
- **前端**: Bootstrap + Highlight.js
- **API**: RESTful API v1

祝您使用愉快！''',
                    category='教程',
                    user_id=admin.id
                )
                db.session.add(sample_doc)
                db.session.commit()
                print("✅ 示例文档创建成功")
            
            # 显示数据库统计
            print("\n📊 数据库统计:")
            print(f"  用户数: {User.query.count()}")
            print(f"  文档数: {Document.query.count()}")
            print(f"  评论数: {Comment.query.count()}")
            
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        print("\n可能的原因:")
        print("1. PostgreSQL服务未启动")
        print("2. 数据库连接信息错误")
        print("3. 数据库用户权限不足")
        print("\n请检查DATABASE_URL环境变量或.env文件配置")
        return False
    
    return True

if __name__ == '__main__':
    print("=== ROS2 Wiki PostgreSQL初始化 ===\n")
    
    # 检查是否强制重建
    if '--reset' in sys.argv:
        print("⚠️  警告: 将删除所有现有数据并重建数据库")
        confirm = input("确定要继续吗? (yes/no): ")
        if confirm.lower() == 'yes':
            with app.app_context():
                db.drop_all()
                print("已删除所有表")
    
    # 初始化数据库
    if init_database():
        print("\n✅ 数据库初始化完成！")
        print(f"\n数据库连接信息: {DATABASE_URL}")
        print("\n下一步:")
        print("1. 启动应用: python3 app.py")
        print("2. 访问: http://localhost:5000")
        print("3. 使用 admin/admin123 登录")
    else:
        sys.exit(1)