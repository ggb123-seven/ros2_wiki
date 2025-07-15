#!/usr/bin/env python3
"""
部署验证脚本 - 检查Render部署配置
在推送到Render前验证配置是否正确
"""

import os
import sys
import subprocess
from pathlib import Path

def check_files():
    """检查必要文件是否存在"""
    print("📁 检查必要文件...")
    
    required_files = [
        'app.py',
        'wsgi.py', 
        'requirements.txt',
        'render.yaml'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"  ✅ {file}")
    
    if missing_files:
        print(f"  ❌ 缺少文件: {', '.join(missing_files)}")
        return False
    
    return True

def check_wsgi():
    """检查wsgi.py语法"""
    print("\n🔍 检查wsgi.py语法...")
    
    try:
        with open('wsgi.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查关键内容
        if 'from app import app' not in content:
            print("  ❌ wsgi.py缺少'from app import app'")
            return False
            
        if 'application = app' not in content:
            print("  ❌ wsgi.py缺少'application = app'")
            return False
            
        print("  ✅ wsgi.py语法正确")
        return True
        
    except Exception as e:
        print(f"  ❌ 读取wsgi.py失败: {e}")
        return False

def check_requirements():
    """检查requirements.txt"""
    print("\n📦 检查requirements.txt...")
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_packages = ['Flask', 'gunicorn']
        missing_packages = []
        
        for package in required_packages:
            if package.lower() not in content.lower():
                missing_packages.append(package)
            else:
                print(f"  ✅ {package}")
        
        if missing_packages:
            print(f"  ❌ 缺少依赖: {', '.join(missing_packages)}")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ 读取requirements.txt失败: {e}")
        return False

def check_render_config():
    """检查render.yaml配置"""
    print("\n⚙️  检查render.yaml配置...")
    
    try:
        with open('render.yaml', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'gunicorn wsgi:app' not in content:
            print("  ❌ render.yaml缺少正确的启动命令")
            return False
            
        if 'pip install -r requirements.txt' not in content:
            print("  ❌ render.yaml缺少构建命令")
            return False
            
        print("  ✅ render.yaml配置正确")
        return True
        
    except Exception as e:
        print(f"  ❌ 读取render.yaml失败: {e}")
        return False

def test_import():
    """测试导入是否正常"""
    print("\n🧪 测试应用导入...")
    
    try:
        # 测试wsgi导入
        import wsgi
        print("  ✅ wsgi.py导入成功")
        
        # 测试应用对象
        if hasattr(wsgi, 'app'):
            print("  ✅ Flask应用对象存在")
        else:
            print("  ❌ Flask应用对象不存在")
            return False
            
        if hasattr(wsgi, 'application'):
            print("  ✅ gunicorn应用对象存在")
        else:
            print("  ❌ gunicorn应用对象不存在")
            return False
            
        return True
        
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("ROS2 Wiki 部署验证脚本")
    print("=" * 50)
    
    checks = [
        check_files,
        check_wsgi, 
        check_requirements,
        check_render_config,
        test_import
    ]
    
    all_passed = True
    
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 所有检查通过！可以安全部署到Render")
        print("\n建议操作:")
        print("1. git add .")
        print("2. git commit -m 'Fix: 简化wsgi.py修复Render部署问题'")
        print("3. git push origin main")
        print("4. 在Render控制台触发重新部署")
    else:
        print("❌ 存在问题，请修复后再部署")
        sys.exit(1)

if __name__ == '__main__':
    main()