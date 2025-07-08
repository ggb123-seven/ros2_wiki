#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加管理员功能
"""
import sqlite3
import os

db_path = 'ros2_wiki.db'

if os.path.exists(db_path):
    print("正在更新数据库结构...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经有is_admin列
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_admin' not in columns:
            # 添加is_admin列
            cursor.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
            print("✓ 添加了is_admin列")
            
            # 将admin用户设置为管理员
            cursor.execute('UPDATE users SET is_admin = 1 WHERE username = "admin"')
            print("✓ 将admin用户设置为管理员")
            
            conn.commit()
            print("数据库更新成功！")
        else:
            print("数据库已经是最新版本")
            
    except Exception as e:
        print(f"更新失败: {e}")
        conn.rollback()
    finally:
        conn.close()
else:
    print("数据库文件不存在，将在首次运行时自动创建")