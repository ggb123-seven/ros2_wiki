#!/usr/bin/env python3
"""
检查管理员账户
"""

import sqlite3
import os

def check_admin_accounts():
    """检查管理员账户"""
    db_path = 'ros2_wiki.db'
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查所有用户
        cursor.execute('SELECT id, username, email, is_admin, created_at FROM users')
        all_users = cursor.fetchall()
        
        print("=== 所有用户账户 ===")
        if all_users:
            for user in all_users:
                admin_status = "👑 管理员" if user[3] else "👤 普通用户"
                print(f"ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 状态: {admin_status}")
        else:
            print("❌ 没有找到任何用户")
        
        # 专门检查管理员
        cursor.execute('SELECT id, username, email FROM users WHERE is_admin = 1')
        admins = cursor.fetchall()
        
        print("\n=== 管理员账户 ===")
        if admins:
            for admin in admins:
                print(f"👑 管理员: {admin[1]} (邮箱: {admin[2]})")
        else:
            print("❌ 没有管理员账户")
            print("\n🔧 解决方案:")
            print("1. 注册一个新账户")
            print("2. 手动设置为管理员")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

def create_admin_account():
    """创建管理员账户"""
    try:
        from werkzeug.security import generate_password_hash
        
        conn = sqlite3.connect('ros2_wiki.db')
        cursor = conn.cursor()
        
        # 创建默认管理员账户
        admin_username = "admin"
        admin_email = "admin@ros2wiki.com"
        admin_password = "admin123"
        
        # 检查是否已存在
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                      (admin_username, admin_email))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️ 用户 {admin_username} 已存在，设置为管理员...")
            cursor.execute('UPDATE users SET is_admin = 1 WHERE username = ? OR email = ?',
                          (admin_username, admin_email))
        else:
            print(f"🔧 创建新管理员账户: {admin_username}")
            password_hash = generate_password_hash(admin_password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin, created_at)
                VALUES (?, ?, ?, 1, datetime('now'))
            ''', (admin_username, admin_email, password_hash))
        
        conn.commit()
        conn.close()
        
        print("✅ 管理员账户创建/更新成功!")
        print(f"👑 用户名: {admin_username}")
        print(f"📧 邮箱: {admin_email}")
        print(f"🔑 密码: {admin_password}")
        print("\n⚠️ 请登录后立即修改密码!")
        
    except Exception as e:
        print(f"❌ 创建管理员账户失败: {e}")

if __name__ == '__main__':
    print("=== ROS2 Wiki 管理员账户检查 ===")
    check_admin_accounts()
    
    print("\n" + "="*50)
    response = input("是否需要创建/设置管理员账户? (y/n): ")
    if response.lower() == 'y':
        create_admin_account()
        print("\n重新检查账户状态:")
        check_admin_accounts()
