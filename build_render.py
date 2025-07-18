#!/usr/bin/env python3
"""
Render平台构建脚本 - 处理数据库初始化错误
"""
import os
import sys
import subprocess

def run_command(cmd, description):
    """运行命令并处理错误"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} 成功")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e}")
        if e.stdout:
            print("标准输出:", e.stdout)
        if e.stderr:
            print("错误输出:", e.stderr)
        return False

def main():
    """主构建流程"""
    print("🚀 开始 Render 平台构建...")
    
    # 1. 安装依赖
    success = run_command(
        "pip install -r requirements_render.txt",
        "安装Python依赖"
    )
    
    if not success:
        print("❌ 依赖安装失败，构建终止")
        sys.exit(1)
    
    # 2. 尝试数据库初始化
    print("\n🗄️ 尝试数据库初始化...")
    db_success = run_command(
        "python cloud_init_db.py",
        "数据库初始化"
    )
    
    if not db_success:
        print("⚠️ 数据库初始化失败，但继续构建过程")
        print("📝 应用将在运行时处理数据库初始化")
    
    # 3. 验证关键文件
    print("\n📋 验证关键文件...")
    critical_files = [
        'app_render.py',
        'templates/base.html',
        'templates/index.html',
        'templates/login.html'
    ]
    
    missing_files = []
    for file in critical_files:
        if os.path.exists(file):
            print(f"✅ {file} 存在")
        else:
            print(f"❌ {file} 缺失")
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️ 缺失关键文件: {', '.join(missing_files)}")
        print("📝 应用可能无法正常运行")
    
    # 4. 环境检查
    print("\n🔍 环境变量检查...")
    env_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'FLASK_ENV',
        'ADMIN_USERNAME',
        'ADMIN_PASSWORD'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var} 已设置")
        else:
            print(f"⚠️ {var} 未设置")
    
    print("\n🎉 构建流程完成!")
    print("📝 即使数据库初始化失败，应用也会尝试在运行时处理")

if __name__ == "__main__":
    main()