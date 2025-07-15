#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加黑名单功能相关字段
用于将现有数据库升级以支持用户黑名单管理功能
"""

import sqlite3
import os
import sys

def check_column_exists(cursor, table_name, column_name):
    """检查表中是否存在指定列"""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    except Exception:
        return False

def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cursor.fetchone() is not None
    except Exception:
        return False

def migrate_database(db_path='ros2_wiki.db'):
    """执行数据库迁移"""
    print(f"开始迁移数据库: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 备份数据库
        backup_path = f"{db_path}.backup"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查并添加用户表的新字段
        migrations_needed = []
        
        if not check_column_exists(cursor, 'users', 'is_blacklisted'):
            migrations_needed.append("ALTER TABLE users ADD COLUMN is_blacklisted BOOLEAN DEFAULT 0")
            
        if not check_column_exists(cursor, 'users', 'blacklisted_at'):
            migrations_needed.append("ALTER TABLE users ADD COLUMN blacklisted_at TIMESTAMP NULL")
            
        if not check_column_exists(cursor, 'users', 'blacklist_reason'):
            migrations_needed.append("ALTER TABLE users ADD COLUMN blacklist_reason TEXT NULL")
            
        if not check_column_exists(cursor, 'users', 'last_seen'):
            migrations_needed.append("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP NULL")
        
        # 执行用户表字段迁移
        for migration in migrations_needed:
            print(f"执行迁移: {migration}")
            cursor.execute(migration)
        
        # 创建user_logs表
        if not check_table_exists(cursor, 'user_logs'):
            print("创建user_logs表...")
            cursor.execute('''
                CREATE TABLE user_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    target_user_id INTEGER,
                    action TEXT NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES users (id),
                    FOREIGN KEY (target_user_id) REFERENCES users (id)
                )
            ''')
        
        conn.commit()
        conn.close()
        
        print("数据库迁移完成!")
        return True
        
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        return False

def verify_migration(db_path='ros2_wiki.db'):
    """验证迁移结果"""
    print("验证迁移结果...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查新字段
        required_columns = ['is_blacklisted', 'blacklisted_at', 'blacklist_reason', 'last_seen']
        for column in required_columns:
            if not check_column_exists(cursor, 'users', column):
                print(f"❌ 字段 {column} 未找到")
                return False
            else:
                print(f"✅ 字段 {column} 存在")
        
        # 检查user_logs表
        if not check_table_exists(cursor, 'user_logs'):
            print("❌ user_logs表未找到")
            return False
        else:
            print("✅ user_logs表存在")
        
        # 检查现有数据完整性
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ 用户数据完整性检查: {user_count} 个用户")
        
        conn.close()
        print("✅ 迁移验证通过!")
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        return False

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'ros2_wiki.db'
    
    print("=== ROS2 Wiki 数据库迁移工具 ===")
    print("添加用户黑名单管理功能支持")
    print()
    
    if migrate_database(db_path):
        if verify_migration(db_path):
            print("\n🎉 迁移成功完成!")
            sys.exit(0)
        else:
            print("\n❌ 迁移验证失败!")
            sys.exit(1)
    else:
        print("\n❌ 迁移失败!")
        sys.exit(1)
