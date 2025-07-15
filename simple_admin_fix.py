#!/usr/bin/env python3
"""
简化版管理员账户修复脚本
使用标准库，无需额外依赖
"""

import urllib.request
import urllib.parse
import urllib.error
import sys
from datetime import datetime

def test_login_page(base_url):
    """测试登录页面"""
    print("🔍 测试登录页面...")
    
    try:
        login_url = f"{base_url}/login"
        response = urllib.request.urlopen(login_url, timeout=30)
        
        if response.getcode() == 200:
            print("✅ 登录页面可访问")
            content = response.read().decode('utf-8')
            
            if 'username' in content.lower() and 'password' in content.lower():
                print("✅ 登录表单元素正常")
                return True
            else:
                print("⚠️ 登录表单元素缺失")
                return False
        else:
            print(f"❌ 登录页面状态码: {response.getcode()}")
            return False
            
    except Exception as e:
        print(f"❌ 登录页面测试失败: {e}")
        return False

def test_admin_login(base_url):
    """测试管理员登录"""
    print("\n🔍 测试管理员登录...")
    
    try:
        # 创建cookie处理器
        import http.cookiejar
        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        
        # 获取登录页面
        login_url = f"{base_url}/login"
        response = opener.open(login_url, timeout=30)
        print(f"✅ 登录页面加载成功 (状态: {response.getcode()})")
        
        # 准备登录数据
        login_data = {
            'username': 'ssss',
            'password': 'ssss123'
        }
        
        # 编码登录数据
        data = urllib.parse.urlencode(login_data).encode('utf-8')
        
        # 创建POST请求
        request = urllib.request.Request(login_url, data=data, method='POST')
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            response = opener.open(request, timeout=30)
            status = response.getcode()
            
            if status == 200:
                content = response.read().decode('utf-8')
                if 'dashboard' in content.lower() or 'admin' in content.lower():
                    print("✅ 登录成功 - 已进入管理区域")
                    return True
                elif 'error' in content.lower() or 'invalid' in content.lower():
                    print("❌ 登录失败 - 凭据无效")
                    return False
                else:
                    print("⚠️ 登录响应不明确")
                    return False
                    
            elif status == 302:
                print("✅ 登录成功 - 服务器重定向")
                return True
            else:
                print(f"⚠️ 登录响应状态: {status}")
                return False
                
        except urllib.error.HTTPError as e:
            if e.code == 302:
                print("✅ 登录成功 - HTTP重定向")
                return True
            else:
                print(f"❌ 登录HTTP错误: {e.code}")
                return False
                
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return False

def check_debug_endpoints(base_url):
    """检查调试端点"""
    print("\n🔍 检查调试端点...")
    
    endpoints = [
        ('/debug/env', '环境变量'),
        ('/debug/db', '数据库状态'),
        ('/debug/admin', '管理员账户')
    ]
    
    for endpoint, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = urllib.request.urlopen(url, timeout=30)
            
            if response.getcode() == 200:
                print(f"✅ {description}: 可访问")
                content = response.read().decode('utf-8')
                
                if endpoint == '/debug/admin':
                    if 'admin_found' in content and 'true' in content.lower():
                        print("   ✅ 找到管理员账户")
                    else:
                        print("   ❌ 未找到管理员账户")
                        
                print(f"   响应: {content[:200]}...")
            else:
                print(f"❌ {description}: 状态码 {response.getcode()}")
                
        except urllib.error.HTTPError as e:
            print(f"❌ {description}: HTTP错误 {e.code}")
        except Exception as e:
            print(f"❌ {description}: {e}")

def test_registration(base_url):
    """尝试注册管理员账户"""
    print("\n🔧 尝试注册管理员账户...")
    
    try:
        register_url = f"{base_url}/register"
        
        # 准备注册数据
        register_data = {
            'username': 'ssss',
            'email': 'seventee_0611@qq.com',
            'password': 'ssss123',
            'confirm_password': 'ssss123'
        }
        
        # 编码数据
        data = urllib.parse.urlencode(register_data).encode('utf-8')
        
        # 创建POST请求
        request = urllib.request.Request(register_url, data=data, method='POST')
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            response = urllib.request.urlopen(request, timeout=30)
            
            if response.getcode() == 200 or response.getcode() == 302:
                print("✅ 注册请求成功发送")
                return True
            else:
                print(f"⚠️ 注册响应状态: {response.getcode()}")
                return False
                
        except urllib.error.HTTPError as e:
            if e.code == 302:
                print("✅ 注册成功 - 服务器重定向")
                return True
            elif e.code == 400:
                print("⚠️ 用户可能已存在")
                return True  # 用户已存在也算成功
            else:
                print(f"❌ 注册HTTP错误: {e.code}")
                return False
                
    except Exception as e:
        print(f"❌ 注册失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python simple_admin_fix.py <应用URL>")
        print("示例: python simple_admin_fix.py https://ros2-wiki.onrender.com")
        return
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🔧 ROS2 Wiki 简化版管理员修复")
    print("="*50)
    print(f"目标应用: {base_url}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试基本功能
    login_page_ok = test_login_page(base_url)
    
    # 检查调试端点
    check_debug_endpoints(base_url)
    
    # 尝试注册（如果登录页面正常）
    if login_page_ok:
        registration_ok = test_registration(base_url)
        
        # 测试登录
        login_ok = test_admin_login(base_url)
        
        if login_ok:
            print("\n🎉 管理员账户验证成功！")
            print("📋 登录信息:")
            print(f"   URL: {base_url}/login")
            print("   用户名: ssss")
            print("   密码: ssss123")
            print("   邮箱: seventee_0611@qq.com")
        else:
            print("\n⚠️ 登录测试失败")
            print("建议:")
            print("1. 检查Render.com部署日志")
            print("2. 验证数据库连接")
            print("3. 确认环境变量设置")
    else:
        print("\n❌ 应用基本功能异常")
        print("请检查应用部署状态")

if __name__ == '__main__':
    main()
