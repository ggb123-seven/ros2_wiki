#!/usr/bin/env python3
"""
测试所有关键路由
"""

import urllib.request
import urllib.error

def test_route(url, description):
    """测试路由"""
    try:
        response = urllib.request.urlopen(url)
        status = response.getcode()
        print(f"✅ {description}: {url} - Status: {status}")
        return True
    except urllib.error.HTTPError as e:
        print(f"⚠️  {description}: {url} - HTTP Error: {e.code}")
        if e.code in [302, 401, 403]:  # 重定向或权限错误是正常的
            print(f"   (这是正常的，需要登录或权限)")
            return True
        return False
    except Exception as e:
        print(f"❌ {description}: {url} - Error: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 测试所有关键路由 ===")
    
    base_url = "http://localhost:5000"
    
    # 测试所有关键路由
    routes_to_test = [
        (f"{base_url}/", "主页"),
        (f"{base_url}/login", "登录页面"),
        (f"{base_url}/register", "注册页面"),
        (f"{base_url}/admin", "管理后台"),
        (f"{base_url}/admin_dashboard", "管理仪表板"),
        (f"{base_url}/admin/users/", "用户管理"),
        (f"{base_url}/admin/users/blacklisted", "黑名单管理"),
        (f"{base_url}/admin/users/audit/logs", "审计日志"),
        (f"{base_url}/admin/users/audit/activity", "活动摘要"),
        (f"{base_url}/documents", "文档列表"),
        (f"{base_url}/search", "搜索页面"),
    ]
    
    success_count = 0
    total_tests = len(routes_to_test)
    
    for url, description in routes_to_test:
        if test_route(url, description):
            success_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"可访问路由: {success_count}/{total_tests}")
    
    if success_count >= total_tests * 0.8:  # 80%以上通过就算成功
        print("🎉 大部分路由正常工作！")
        print("\n📋 访问指南:")
        print("1. 主页: http://localhost:5000/")
        print("2. 登录: http://localhost:5000/login")
        print("3. 注册: http://localhost:5000/register")
        print("4. 管理后台: http://localhost:5000/admin")
        print("5. 用户管理: http://localhost:5000/admin/users/")
    else:
        print("❌ 多个路由无法访问，需要检查服务器配置")
    
    return success_count >= total_tests * 0.8

if __name__ == '__main__':
    main()
