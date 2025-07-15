#!/usr/bin/env python3
"""
检查管理员密码并提供登录信息
"""

import sqlite3
from werkzeug.security import check_password_hash

def check_admin_login():
    """检查管理员登录信息"""
    try:
        conn = sqlite3.connect('ros2_wiki.db')
        cursor = conn.cursor()
        
        # 获取管理员信息
        cursor.execute('SELECT username, email, password_hash FROM users WHERE is_admin = 1')
        admin = cursor.fetchone()
        
        if admin:
            username, email, password_hash = admin
            
            print("=== 管理员账户信息 ===")
            print(f"👑 用户名: {username}")
            print(f"📧 邮箱: {email}")
            
            # 测试常见密码
            common_passwords = ['admin123', 'password', 'admin', '123456', 'password123']
            
            print("\n🔑 测试常见密码:")
            password_found = False
            
            for pwd in common_passwords:
                if check_password_hash(password_hash, pwd):
                    print(f"✅ 密码是: {pwd}")
                    password_found = True
                    break
            
            if not password_found:
                print("❌ 密码不是常见密码")
                print("💡 可能需要重置密码")
            
            print(f"\n🌐 登录地址: http://localhost:5000/login")
            print(f"👤 用户名: {username}")
            print(f"📧 或邮箱: {email}")
            
        else:
            print("❌ 没有找到管理员账户")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

def reset_admin_password():
    """重置管理员密码"""
    try:
        # 导入werkzeug.security模块中的generate_password_hash函数
        from werkzeug.security import generate_password_hash
        
        # 连接到ros2_wiki.db数据库
        conn = sqlite3.connect('ros2_wiki.db')
        # 创建游标
        cursor = conn.cursor()
        
        # 设置新密码
        new_password = "admin123"
        # 生成新密码的哈希值
        password_hash = generate_password_hash(new_password)
        
        # 更新管理员密码
        cursor.execute('UPDATE users SET password_hash = ? WHERE is_admin = 1', (password_hash,))
        # 提交更改
        conn.commit()
        # 关闭数据库连接
        conn.close()
        
        # 打印成功信息
        print("✅ 管理员密码已重置!")
        print(f"🔑 新密码: {new_password}")
        print("⚠️ 请登录后立即修改密码!")
        
    except Exception as e:
        # 打印错误信息
        print(f"❌ 重置密码失败: {e}")

if __name__ == '__main__':
    print("=== 管理员登录信息检查 ===")
    check_admin_login()
    
    print("\n" + "="*50)
    response = input("是否需要重置管理员密码为 'admin123'? (y/n): ")
    if response.lower() == 'y':
        reset_admin_password()
        print("\n重新检查登录信息:")
        check_admin_login()
