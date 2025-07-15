#!/usr/bin/env python3
"""
测试ssss账户登录功能
"""

import sqlite3
from werkzeug.security import check_password_hash

def test_ssss_login():
    """测试ssss账户登录"""
    print("=== 测试ssss账户登录功能 ===")
    
    try:
        conn = sqlite3.connect('ros2_wiki.db')
        cursor = conn.cursor()
        
        # 获取ssss用户信息
        cursor.execute('SELECT * FROM users WHERE username = "ssss"')
        user = cursor.fetchone()
        
        if not user:
            print("❌ 未找到ssss用户")
            return False
        
        print(f"✅ 找到用户: {user[1]} ({user[2]})")
        print(f"管理员权限: {'是' if user[4] else '否'}")
        print(f"账户状态: {'正常' if not user[6] else '已拉黑'}")
        
        # 测试常见密码
        test_passwords = [
            'admin123', 'ssss', 'password', '123456', 
            'ssss123', 'seventee', '0611', 'seventee_0611'
        ]
        
        print(f"\n🔑 测试密码验证:")
        password_found = False
        
        for pwd in test_passwords:
            try:
                if check_password_hash(user[3], pwd):
                    print(f"✅ 密码 '{pwd}' 验证成功!")
                    password_found = True
                    
                    # 模拟完整登录流程测试
                    print(f"\n🧪 模拟登录流程测试:")
                    print(f"1. 用户名验证: ✅ {user[1]}")
                    print(f"2. 密码验证: ✅ 通过")
                    print(f"3. 账户状态: ✅ {'正常' if not user[6] else '已拉黑'}")
                    print(f"4. 管理员权限: ✅ {'有' if user[4] else '无'}")
                    
                    break
                else:
                    print(f"❌ 密码 '{pwd}' 验证失败")
            except Exception as e:
                print(f"❌ 密码 '{pwd}' 验证出错: {e}")
        
        if not password_found:
            print(f"\n⚠️ 未找到正确密码，可能需要重置")
            print(f"建议尝试以下操作:")
            print(f"1. 检查备份数据库中的原始密码哈希")
            print(f"2. 重置为已知密码")
        
        conn.close()
        return password_found
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def reset_ssss_password():
    """重置ssss密码为已知密码"""
    print("\n=== 重置ssss密码 ===")
    
    try:
        from werkzeug.security import generate_password_hash
        
        conn = sqlite3.connect('ros2_wiki.db')
        cursor = conn.cursor()
        
        # 重置为简单密码
        new_password = "ssss123"
        password_hash = generate_password_hash(new_password)
        
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = "ssss"', (password_hash,))
        conn.commit()
        conn.close()
        
        print(f"✅ ssss账户密码已重置为: {new_password}")
        print(f"🌐 现在可以使用以下信息登录:")
        print(f"   地址: http://localhost:5000/login")
        print(f"   用户名: ssss")
        print(f"   密码: {new_password}")
        
        return True
        
    except Exception as e:
        print(f"❌ 密码重置失败: {e}")
        return False

if __name__ == '__main__':
    success = test_ssss_login()
    
    if not success:
        print("\n" + "="*50)
        response = input("是否重置ssss密码为已知密码? (y/n): ")
        if response.lower() == 'y':
            reset_ssss_password()
            print("\n重新测试登录:")
            test_ssss_login()
