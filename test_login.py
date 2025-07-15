#!/usr/bin/env python3
"""
测试登录功能
"""

import urllib.request
import urllib.parse
import http.cookiejar

def test_login():
    """测试管理员登录"""
    try:
        # 创建cookie jar来保持会话
        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        
        # 1. 先访问登录页面获取表单
        print("1. 访问登录页面...")
        login_url = "http://localhost:5000/login"
        response = opener.open(login_url)
        print(f"✅ 登录页面状态: {response.getcode()}")
        
        # 2. 准备登录数据
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # 3. 发送登录请求
        print("2. 尝试登录...")
        data = urllib.parse.urlencode(login_data).encode('utf-8')
        request = urllib.request.Request(login_url, data=data, method='POST')
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        response = opener.open(request)
        print(f"✅ 登录请求状态: {response.getcode()}")
        
        # 4. 测试访问管理后台
        print("3. 测试管理后台访问...")
        admin_url = "http://localhost:5000/admin_dashboard"
        admin_response = opener.open(admin_url)
        print(f"✅ 管理后台状态: {admin_response.getcode()}")
        
        # 5. 测试用户管理页面
        print("4. 测试用户管理页面...")
        users_url = "http://localhost:5000/admin/users/"
        users_response = opener.open(users_url)
        print(f"✅ 用户管理页面状态: {users_response.getcode()}")
        
        print("\n🎉 登录测试成功！管理员账户工作正常！")
        return True
        
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return False

def verify_admin_in_db():
    """验证数据库中的管理员账户"""
    try:
        import sqlite3
        from werkzeug.security import check_password_hash
        
        conn = sqlite3.connect('ros2_wiki.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, email, password_hash, is_admin FROM users WHERE username = "admin"')
        admin = cursor.fetchone()
        
        if admin:
            username, email, password_hash, is_admin = admin
            print("=== 数据库验证 ===")
            print(f"用户名: {username}")
            print(f"邮箱: {email}")
            print(f"管理员权限: {'是' if is_admin else '否'}")
            
            # 验证密码
            if check_password_hash(password_hash, 'admin123'):
                print("✅ 密码验证: 正确")
            else:
                print("❌ 密码验证: 错误")
            
            conn.close()
            return True
        else:
            print("❌ 数据库中没有找到admin用户")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False

if __name__ == '__main__':
    print("=== 管理员登录测试 ===")
    
    # 先验证数据库
    if verify_admin_in_db():
        print("\n" + "="*40)
        # 再测试登录
        test_login()
    else:
        print("请先运行 reset_admin.py 重置管理员账户")
