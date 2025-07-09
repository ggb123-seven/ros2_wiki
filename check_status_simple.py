#!/usr/bin/env python3
"""
简化版数据库状态检查（无需额外依赖）
"""
import os
import sqlite3

print("="*50)
print("ROS2 Wiki 数据库迁移状态")
print("="*50)

# 1. 检查SQLite
print("\n1. SQLite数据库检查:")
if os.path.exists('ros2_wiki.db'):
    try:
        conn = sqlite3.connect('ros2_wiki.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM documents")
        docs = cursor.fetchone()[0]
        print(f"✅ SQLite数据库存在")
        print(f"   - 用户数: {users}")
        print(f"   - 文档数: {docs}")
        conn.close()
    except Exception as e:
        print(f"❌ SQLite数据库错误: {e}")
else:
    print("⚠️  SQLite数据库不存在")

# 2. 检查环境配置
print("\n2. PostgreSQL配置检查:")
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        content = f.read()
        if 'postgresql://' in content:
            print("✅ PostgreSQL配置已设置")
            for line in content.split('\n'):
                if 'DATABASE_URL' in line and 'postgresql' in line:
                    print(f"   {line.strip()}")
        else:
            print("⚠️  仍在使用SQLite配置")
else:
    print("❌ .env文件不存在")

# 3. 检查必要文件
print("\n3. 迁移文件检查:")
files = {
    'app_postgres.py': '✅ PostgreSQL版本应用',
    'scripts/migrate_to_postgres.py': '✅ 数据迁移脚本',
    'scripts/init_postgres_db.py': '✅ 数据库初始化脚本',
    'migrate_helper.sh': '✅ 迁移助手'
}

for file, desc in files.items():
    if os.path.exists(file):
        print(f"{desc}: {file}")
    else:
        print(f"❌ 缺少: {file}")

# 4. 下一步建议
print("\n" + "="*50)
print("下一步操作:")
print("1. 如果尚未安装依赖包:")
print("   请先安装: pip install -r requirements.txt")
print("\n2. 运行迁移助手:")
print("   ./migrate_helper.sh")
print("\n3. 选择合适的选项:")
print("   - 选项1: 初始化新的PostgreSQL数据库")
print("   - 选项3: 测试PostgreSQL连接")
print("   - 选项4: 启动PostgreSQL版本应用")
print("="*50)