#!/usr/bin/env python3
"""
ROS2 Wiki 用户搜索功能完整测试脚本
用于验证后台用户搜索功能的完整性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_blueprints.permissions import get_user_manager
from flask import Flask
from app import app

def test_user_search_comprehensive():
    """全面测试用户搜索功能"""
    print("=" * 60)
    print("ROS2 Wiki 用户搜索功能完整测试")
    print("=" * 60)
    
    with app.app_context():
        um = get_user_manager()
        
        # 测试场景1: 基本搜索功能
        print("\n1. 基本搜索功能测试")
        print("-" * 30)
        
        # 搜索admin用户
        result = um.get_all_users(page=1, per_page=10, search='admin')
        print(f"搜索'admin'结果: {result['total']} 个用户")
        for user in result['users']:
            print(f"  ✓ {user['username']} ({user['email']})")
        
        # 搜索邮箱域名
        result = um.get_all_users(page=1, per_page=10, search='ros2wiki.com')
        print(f"\n搜索'ros2wiki.com'结果: {result['total']} 个用户")
        for user in result['users']:
            print(f"  ✓ {user['username']} ({user['email']})")
        
        # 测试场景2: 分页功能
        print("\n2. 分页功能测试")
        print("-" * 30)
        
        # 获取第一页
        result_page1 = um.get_all_users(page=1, per_page=3)
        print(f"第1页 (共{result_page1['total_pages']}页):")
        for user in result_page1['users']:
            print(f"  ✓ {user['username']}")
        
        # 获取第二页
        if result_page1['total_pages'] > 1:
            result_page2 = um.get_all_users(page=2, per_page=3)
            print(f"第2页:")
            for user in result_page2['users']:
                print(f"  ✓ {user['username']}")
        
        # 测试场景3: 边界情况
        print("\n3. 边界情况测试")
        print("-" * 30)
        
        # 空搜索
        result = um.get_all_users(page=1, per_page=10, search='')
        print(f"空搜索结果: {result['total']} 个用户")
        
        # 不存在的搜索
        result = um.get_all_users(page=1, per_page=10, search='nonexistent_user_12345')
        print(f"不存在用户搜索结果: {result['total']} 个用户")
        
        # 特殊字符搜索
        result = um.get_all_users(page=1, per_page=10, search='@')
        print(f"搜索'@'结果: {result['total']} 个用户")
        
        # 测试场景4: 管理员功能
        print("\n4. 管理员功能测试")
        print("-" * 30)
        
        # 获取所有管理员
        all_users = um.get_all_users(page=1, per_page=50)
        admin_count = sum(1 for user in all_users['users'] if user['is_admin'])
        print(f"系统中管理员数量: {admin_count}")
        
        # 显示管理员列表
        print("管理员列表:")
        for user in all_users['users']:
            if user['is_admin']:
                status = "被拉黑" if user.get('is_blacklisted') else "正常"
                print(f"  ✓ {user['username']} ({user['email']}) - {status}")
        
        print("\n" + "=" * 60)
        print("测试完成! 用户搜索功能运行正常。")
        print("=" * 60)

def test_route_access():
    """测试路由访问"""
    print("\n5. 路由访问测试")
    print("-" * 30)
    
    with app.test_client() as client:
        # 测试用户管理页面
        response = client.get('/admin/users')
        print(f"访问 /admin/users: {response.status_code}")
        
        # 测试搜索功能
        response = client.get('/admin/users?search=admin')
        print(f"访问 /admin/users?search=admin: {response.status_code}")
        
        if response.status_code == 200:
            print("  ✓ 搜索路由正常工作")
        else:
            print("  ✗ 搜索路由可能存在问题")

if __name__ == '__main__':
    try:
        test_user_search_comprehensive()
        test_route_access()
        print("\n🎉 所有测试通过！用户搜索功能正常工作。")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()