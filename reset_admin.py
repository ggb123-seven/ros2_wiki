#!/usr/bin/env python3
"""
重置管理员账户
"""

import sqlite3
from werkzeug.security import generate_password_hash

def reset_admin():
    """重置管理员账户"""
    try:
        conn = sqlite3.connect('ros2_wiki.db')
        cursor = conn.cursor()
        
        # 删除所有现有管理员
        cursor.execute('DELETE FROM users WHERE username = "admin"')
        
        # 创建新的管理员账户
        username = "admin"
        email = "admin@ros2wiki.com"
        password = "admin123"
        password_hash = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted, created_at)
            VALUES (?, ?, ?, 1, 0, datetime('now'))
        ''', (username, email, password_hash))
        
        conn.commit()
        
        # 验证创建成功
        cursor.execute('SELECT id, username, email, is_admin FROM users WHERE username = ?', (username,))
        admin = cursor.fetchone()
        
        if admin:
            print("✅ 管理员账户重置成功！")
            print(f"ID: {admin[0]}")
            print(f"用户名: {admin[1]}")
            print(f"邮箱: {admin[2]}")
            print(f"管理员权限: {'是' if admin[3] else '否'}")
            print(f"密码: {password}")
            print("\n🌐 登录信息:")
            print(f"地址: http://localhost:5000/login")
            print(f"用户名: {username}")
            print(f"密码: {password}")
        else:
            print("❌ 创建失败")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 重置失败: {e}")

if __name__ == '__main__':
    print("=== 重置管理员账户 ===")
    reset_admin()
