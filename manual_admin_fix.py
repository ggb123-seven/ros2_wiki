#!/usr/bin/env python3
"""
手动修复云端管理员账户
针对Render.com部署的紧急修复脚本
"""

import os
import sys
import requests
import json
from datetime import datetime

def create_admin_via_api(base_url):
    """通过API创建管理员账户"""
    print("🔧 尝试通过API创建管理员账户...")
    
    try:
        # 准备管理员数据
        admin_data = {
            'username': 'ssss',
            'email': 'seventee_0611@qq.com',
            'password': 'ssss123',
            'is_admin': True
        }
        
        # 尝试注册API端点
        register_url = f"{base_url}/register"
        
        response = requests.post(register_url, data=admin_data, timeout=30)
        
        if response.status_code == 200 or response.status_code == 302:
            print("✅ 管理员账户创建成功！")
            return True
        else:
            print(f"⚠️ 注册响应状态: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API创建失败: {e}")
        return False

def test_admin_login(base_url):
    """测试管理员登录"""
    print("\n🔍 测试管理员登录...")
    
    try:
        session = requests.Session()
        
        # 获取登录页面
        login_url = f"{base_url}/login"
        response = session.get(login_url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ 无法访问登录页面: {response.status_code}")
            return False
        
        # 尝试登录
        login_data = {
            'username': 'ssss',
            'password': 'ssss123'
        }
        
        response = session.post(login_url, data=login_data, timeout=30)
        
        # 检查登录结果
        if response.status_code == 200:
            if 'dashboard' in response.text.lower() or 'admin' in response.text.lower():
                print("✅ 管理员登录成功！")
                return True
            elif 'error' in response.text.lower() or 'invalid' in response.text.lower():
                print("❌ 登录失败 - 凭据无效")
                return False
        elif response.status_code == 302:
            # 检查重定向
            location = response.headers.get('Location', '')
            if 'dashboard' in location or 'admin' in location:
                print("✅ 登录成功 - 重定向到管理区域")
                return True
            else:
                print(f"⚠️ 重定向到: {location}")
                return False
        
        print(f"⚠️ 登录响应状态: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return False

def check_debug_endpoints(base_url):
    """检查调试端点"""
    print("\n🔍 检查调试端点...")
    
    endpoints = [
        '/debug/env',
        '/debug/db', 
        '/debug/admin'
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: 可访问")
                try:
                    data = response.json()
                    if endpoint == '/debug/admin':
                        if data.get('admin_found'):
                            print(f"   管理员账户: {data.get('username')}")
                            print(f"   邮箱: {data.get('email')}")
                            print(f"   管理员权限: {data.get('is_admin')}")
                        else:
                            print("   ❌ 未找到管理员账户")
                except:
                    print(f"   响应内容: {response.text[:100]}...")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def main():
    """主修复函数"""
    if len(sys.argv) < 2:
        print("使用方法: python manual_admin_fix.py <应用URL>")
        print("示例: python manual_admin_fix.py https://ros2-wiki-xxx.onrender.com")
        return
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🔧 ROS2 Wiki 管理员账户手动修复")
    print("="*50)
    print(f"目标应用: {base_url}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查调试端点
    check_debug_endpoints(base_url)
    
    # 尝试创建管理员账户
    if create_admin_via_api(base_url):
        # 测试登录
        if test_admin_login(base_url):
            print("\n🎉 管理员账户修复成功！")
            print("📋 登录信息:")
            print("   URL: " + base_url + "/login")
            print("   用户名: ssss")
            print("   密码: ssss123")
            print("   邮箱: seventee_0611@qq.com")
        else:
            print("\n⚠️ 账户创建成功但登录测试失败")
    else:
        print("\n❌ 管理员账户创建失败")
        print("请检查:")
        print("1. 应用是否正常运行")
        print("2. 数据库连接是否正常")
        print("3. 环境变量是否正确设置")

if __name__ == '__main__':
    main()
