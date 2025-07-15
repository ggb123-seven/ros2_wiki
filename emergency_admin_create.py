#!/usr/bin/env python3
"""
紧急管理员账户创建脚本
直接连接数据库创建管理员账户
"""

import os
import sys
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_account():
    """创建管理员账户"""
    print("🚑 紧急创建管理员账户...")
    
    try:
        # 导入数据库模块
        from app import get_db_connection
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 管理员信息
        admin_username = 'ssss'
        admin_email = 'seventee_0611@qq.com'
        admin_password = 'Ssss123!'
        
        # 检查管理员是否已存在
        if 'postgresql' in os.environ.get('DATABASE_URL', ''):
            cursor.execute('SELECT id FROM users WHERE username = %s OR email = %s', 
                          (admin_username, admin_email))
        else:
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                          (admin_username, admin_email))
        
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"✅ 管理员账户已存在 (ID: {existing_user[0]})")
            
            # 更新现有账户确保管理员权限
            password_hash = generate_password_hash(admin_password)
            
            if 'postgresql' in os.environ.get('DATABASE_URL', ''):
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = %s, is_admin = TRUE, is_blacklisted = FALSE
                    WHERE username = %s OR email = %s
                ''', (password_hash, admin_username, admin_email))
            else:
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, is_admin = 1, is_blacklisted = 0
                    WHERE username = ? OR email = ?
                ''', (password_hash, admin_username, admin_email))
            
            conn.commit()
            print("✅ 管理员权限已更新")
            
        else:
            # 创建新的管理员账户
            password_hash = generate_password_hash(admin_password)
            
            if 'postgresql' in os.environ.get('DATABASE_URL', ''):
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted, created_at)
                    VALUES (%s, %s, %s, TRUE, FALSE, %s)
                ''', (admin_username, admin_email, password_hash, datetime.now()))
            else:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted, created_at)
                    VALUES (?, ?, ?, 1, 0, ?)
                ''', (admin_username, admin_email, password_hash, datetime.now()))
            
            conn.commit()
            print("✅ 新管理员账户已创建")
        
        # 验证账户
        if 'postgresql' in os.environ.get('DATABASE_URL', ''):
            cursor.execute('''
                SELECT username, email, is_admin, created_at 
                FROM users WHERE username = %s
            ''', (admin_username,))
        else:
            cursor.execute('''
                SELECT username, email, is_admin, created_at 
                FROM users WHERE username = ?
            ''', (admin_username,))
        
        admin = cursor.fetchone()
        
        if admin:
            print("\n✅ 管理员账户验证:")
            print(f"   用户名: {admin[0]}")
            print(f"   邮箱: {admin[1]}")
            print(f"   管理员权限: {admin[2]}")
            print(f"   创建时间: {admin[3]}")
            
            cursor.close()
            conn.close()
            
            print("\n🎉 管理员账户创建/修复完成!")
            print("📋 登录信息:")
            print("   用户名: ssss")
            print("   密码: Ssss123!")
            print("   邮箱: seventee_0611@qq.com")
            
            return True
        else:
            print("❌ 账户验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 创建管理员账户失败: {e}")
        return False

def test_local_login():
    """测试本地登录功能"""
    print("\n🔍 测试登录功能...")
    
    try:
        from werkzeug.security import check_password_hash
        from app import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取管理员账户
        if 'postgresql' in os.environ.get('DATABASE_URL', ''):
            cursor.execute('SELECT password_hash FROM users WHERE username = %s', ('ssss',))
        else:
            cursor.execute('SELECT password_hash FROM users WHERE username = ?', ('ssss',))
        
        result = cursor.fetchone()
        
        if result:
            password_hash = result[0]
            if check_password_hash(password_hash, 'ssss123'):
                print("✅ 密码验证成功!")
                return True
            else:
                print("❌ 密码验证失败!")
                return False
        else:
            print("❌ 未找到管理员账户!")
            return False
            
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚑 ROS2 Wiki 紧急管理员修复")
    print("="*40)
    
    # 设置环境变量
    os.environ['AUTO_CREATE_ADMIN'] = 'true'
    os.environ['ADMIN_USERNAME'] = 'ssss'
    os.environ['ADMIN_EMAIL'] = 'seventee_0611@qq.com'
    os.environ['ADMIN_PASSWORD'] = 'Ssss123!'
    
    # 创建管理员账户
    if create_admin_account():
        # 测试登录
        if test_local_login():
            print("\n🎉 所有测试通过!")
            print("现在您可以使用 ssss/Ssss123! 登录应用了!")
        else:
            print("\n⚠️ 账户创建成功但登录测试失败")
    else:
        print("\n❌ 管理员账户创建失败")

if __name__ == '__main__':
    main()
