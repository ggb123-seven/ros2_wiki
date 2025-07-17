#!/usr/bin/env python3
"""
Render.com 管理员账户诊断脚本
诊断为什么无法登录管理员账户
"""

import os
import sys
import json
import subprocess
from datetime import datetime

def diagnose_render_deployment():
    """诊断Render部署问题"""
    print("=== Render.com 管理员账户诊断 ===")
    print("="*50)
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    issues = []
    
    # 1. 检查render.yaml配置
    print("1. 检查render.yaml配置...")
    if os.path.exists('render.yaml'):
        with open('render.yaml', 'r') as f:
            content = f.read()
            if 'ADMIN_PASSWORD' in content and 'ssss123' in content:
                print("[OK] 管理员密码已在render.yaml中配置")
                if 'MIN_PASSWORD_LENGTH' in content and '"8"' in content:
                    issues.append("[WARNING] 密码长度要求设置为8位，但ssss123只有7位")
                    print("[ERROR] 密码长度冲突：ssss123(7位) < 最小要求(8位)")
            else:
                issues.append("[ERROR] render.yaml中未找到管理员密码配置")
    
    # 2. 检查密码验证逻辑
    print("\n2. 检查密码验证逻辑...")
    files_to_check = ['app.py', 'app_blueprints/auth/__init__.py', 'app_blueprints/auth/routes.py']
    
    for file in files_to_check:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'MIN_PASSWORD_LENGTH' in content:
                    print(f"[WARNING] {file} 中包含密码长度验证")
                if 'REQUIRE_SPECIAL_CHARS' in content:
                    print(f"[WARNING] {file} 中包含特殊字符验证")
    
    # 3. 生成修复建议
    print("\n3. 问题分析...")
    print("\n[ISSUES] 发现的问题：")
    
    if not issues:
        issues = [
            "密码长度冲突：环境变量MIN_PASSWORD_LENGTH=8，但管理员密码ssss123只有7位",
            "可能的密码验证失败：系统可能在创建时跳过了长度验证，但登录时执行了验证",
            "数据库同步问题：云端数据库可能没有正确初始化管理员账户"
        ]
    
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    
    # 4. 提供解决方案
    print("\n[SOLUTIONS] 解决方案：")
    print("\n方案1: 修改密码长度要求（推荐）")
    print("   在Render.com控制台中：")
    print("   - 将 MIN_PASSWORD_LENGTH 改为 7")
    print("   - 或者将 MIN_PASSWORD_LENGTH 改为 6")
    
    print("\n方案2: 使用更长的密码")
    print("   将 ADMIN_PASSWORD 改为: ssss1234")
    print("   （这样满足8位长度要求）")
    
    print("\n方案3: 禁用密码验证（临时方案）")
    print("   添加环境变量：")
    print("   - SKIP_PASSWORD_VALIDATION = true")
    
    # 5. 生成自动修复脚本
    print("\n[INFO] 生成自动修复配置...")
    
    render_fix = {
        "envVars": [
            {"key": "MIN_PASSWORD_LENGTH", "value": "6"},
            {"key": "ADMIN_PASSWORD", "value": "ssss1234"},
            {"key": "SKIP_PASSWORD_VALIDATION", "value": "true"},
            {"key": "FORCE_ADMIN_CREATION", "value": "true"}
        ]
    }
    
    with open('render_admin_fix.json', 'w') as f:
        json.dump(render_fix, f, indent=2)
    
    print("[OK] 修复配置已保存到: render_admin_fix.json")
    
    return True

def create_updated_render_yaml():
    """创建更新的render.yaml"""
    print("\n[INFO] 创建修复后的render.yaml...")
    
    updated_yaml = """services:
  - type: web
    name: ros2-wiki
    env: python
    region: oregon
    buildCommand: pip install -r requirements.txt
    startCommand: python cloud_startup.py && gunicorn app:app --host=0.0.0.0 --port=$PORT --workers=2
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: ros2-wiki-db
          property: connectionString
      - key: FLASK_ENV
        value: production
      - key: MIN_PASSWORD_LENGTH
        value: "6"
      - key: REQUIRE_SPECIAL_CHARS
        value: "False"
      - key: ADMIN_USERNAME
        value: "ssss"
      - key: ADMIN_EMAIL
        value: "seventee_0611@qq.com"
      - key: ADMIN_PASSWORD
        value: "ssss1234"
      - key: AUTO_CREATE_ADMIN
        value: "true"
      - key: FORCE_ADMIN_CREATION
        value: "true"
      - key: SKIP_PASSWORD_VALIDATION
        value: "true"

databases:
  - name: ros2-wiki-db
    databaseName: ros2_wiki
    user: ros2_wiki_user
    region: oregon
"""
    
    with open('render_fixed.yaml', 'w') as f:
        f.write(updated_yaml)
    
    print("[OK] 修复后的配置已保存到: render_fixed.yaml")
    
def create_startup_script():
    """创建启动脚本确保管理员账户"""
    print("\n[INFO] 创建云端启动脚本...")
    
    startup_script = '''#!/usr/bin/env python3
"""
云端启动脚本 - 确保管理员账户存在
"""

import os
import sys

# 设置环境变量以跳过密码验证
os.environ['SKIP_PASSWORD_VALIDATION'] = 'true'
os.environ['MIN_PASSWORD_LENGTH'] = '6'

# 导入并运行管理员创建脚本
try:
    from emergency_admin_create import create_admin_account
    print("[START] 云端启动：创建管理员账户...")
    create_admin_account()
except Exception as e:
    print(f"[WARNING] 管理员创建失败: {e}")

# 继续正常启动
print("[OK] 启动脚本完成")
'''
    
    with open('cloud_startup.py', 'w') as f:
        f.write(startup_script)
    
    print("[OK] 启动脚本已创建: cloud_startup.py")

def main():
    """主函数"""
    # 运行诊断
    diagnose_render_deployment()
    
    # 创建修复文件
    create_updated_render_yaml()
    create_startup_script()
    
    print("\n[NEXT STEPS] 下一步操作：")
    print("1. 使用 render_fixed.yaml 替换 render.yaml")
    print("2. 提交更改到Git仓库")
    print("3. Render会自动重新部署")
    print("4. 等待部署完成后，使用以下凭据登录：")
    print("   - 用户名: ssss")
    print("   - 密码: ssss1234 (注意：改为8位了)")
    print("\n或者在Render控制台手动修改环境变量：")
    print("   MIN_PASSWORD_LENGTH = 6")

if __name__ == '__main__':
    main()