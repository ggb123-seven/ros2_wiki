#!/usr/bin/env python3
"""
紧急恢复管理员账户
优先恢复用户的管理员权限
"""

import sqlite3
import shutil
from datetime import datetime

def restore_admin_account():
    """恢复管理员账户"""
    print("=== 紧急恢复管理员账户 ===")
    
    try:
        # 1. 创建当前数据库备份
        backup_path = f"ros2_wiki.db.emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2('ros2_wiki.db', backup_path)
        print(f"✅ 当前数据库已备份到: {backup_path}")
        
        # 2. 连接备份和当前数据库
        backup_conn = sqlite3.connect('ros2_wiki.db.backup')
        current_conn = sqlite3.connect('ros2_wiki.db')
        
        backup_cursor = backup_conn.cursor()
        current_cursor = current_conn.cursor()
        
        # 3. 查找备份中的管理员账户
        print("\n=== 查找备份中的管理员账户 ===")
        backup_cursor.execute('SELECT * FROM users WHERE is_admin = 1')
        admin_users = backup_cursor.fetchall()
        
        for user in admin_users:
            print(f"发现管理员: ID={user[0]}, 用户名={user[1]}, 邮箱={user[2]}")
        
        # 4. 特别查找ssss用户（可能是管理员）
        backup_cursor.execute('SELECT * FROM users WHERE username = "ssss" OR email LIKE "%seventee_0611%"')
        target_user = backup_cursor.fetchone()
        
        if target_user:
            print(f"\n🎯 找到目标用户: {target_user[1]} ({target_user[2]})")
            
            # 检查当前数据库是否已存在该用户
            current_cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                                 (target_user[1], target_user[2]))
            existing = current_cursor.fetchone()
            
            if existing:
                print(f"⚠️ 用户已存在，更新为管理员权限...")
                current_cursor.execute('''
                    UPDATE users SET 
                        is_admin = 1,
                        password_hash = ?,
                        email = ?,
                        created_at = ?,
                        is_blacklisted = 0
                    WHERE username = ?
                ''', (target_user[3], target_user[2], target_user[5], target_user[1]))
            else:
                print(f"✅ 恢复用户并设置为管理员...")
                current_cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted, 
                                     blacklisted_at, blacklist_reason, last_seen, created_at)
                    VALUES (?, ?, ?, 1, 0, NULL, NULL, NULL, ?)
                ''', (target_user[1], target_user[2], target_user[3], target_user[5]))
            
            current_conn.commit()
            print(f"🎉 用户 {target_user[1]} 已恢复并设置为管理员！")
        
        # 5. 恢复其他管理员账户
        print("\n=== 恢复其他管理员账户 ===")
        for admin_user in admin_users:
            username = admin_user[1]
            if username == 'ssss':  # 已经处理过
                continue
                
            # 检查是否与当前admin冲突
            current_cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if current_cursor.fetchone():
                print(f"⚠️ 管理员 {username} 已存在，跳过")
                continue
            
            print(f"恢复管理员: {username}")
            current_cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted,
                                 blacklisted_at, blacklist_reason, last_seen, created_at)
                VALUES (?, ?, ?, 1, 0, NULL, NULL, NULL, ?)
            ''', (admin_user[1], admin_user[2], admin_user[3], admin_user[5]))
        
        current_conn.commit()
        
        # 6. 验证恢复结果
        print("\n=== 验证恢复结果 ===")
        current_cursor.execute('SELECT username, email, is_admin FROM users WHERE is_admin = 1')
        admins = current_cursor.fetchall()
        
        print("当前管理员账户:")
        for admin in admins:
            print(f"  👑 {admin[0]} ({admin[1]})")
        
        backup_conn.close()
        current_conn.close()
        
        print(f"\n🎉 管理员账户恢复完成！")
        print(f"📋 总共恢复了 {len(admins)} 个管理员账户")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

if __name__ == '__main__':
    restore_admin_account()
