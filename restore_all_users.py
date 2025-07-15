#!/usr/bin/env python3
"""
恢复所有用户账户
"""

import sqlite3

def restore_all_users():
    """恢复所有用户账户"""
    print("=== 恢复所有用户账户 ===")
    
    try:
        backup_conn = sqlite3.connect('ros2_wiki.db.backup')
        current_conn = sqlite3.connect('ros2_wiki.db')
        
        backup_cursor = backup_conn.cursor()
        current_cursor = current_conn.cursor()
        
        # 获取备份中的所有用户
        backup_cursor.execute('SELECT * FROM users')
        backup_users = backup_cursor.fetchall()
        
        print(f"备份中共有 {len(backup_users)} 个用户")
        
        # 获取当前用户列表
        current_cursor.execute('SELECT username FROM users')
        current_usernames = [row[0] for row in current_cursor.fetchall()]
        
        print(f"当前数据库中有 {len(current_usernames)} 个用户: {current_usernames}")
        
        # 恢复缺失的用户
        restored_count = 0
        for user in backup_users:
            username = user[1]
            
            if username in current_usernames:
                print(f"⚠️ 用户 {username} 已存在，跳过")
                continue
            
            try:
                # 恢复用户，保持原有权限
                current_cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted,
                                     blacklisted_at, blacklist_reason, last_seen, created_at)
                    VALUES (?, ?, ?, ?, 0, NULL, NULL, NULL, ?)
                ''', (user[1], user[2], user[3], user[4], user[5]))
                
                user_type = "管理员" if user[4] else "普通用户"
                print(f"✅ 恢复{user_type}: {username} ({user[2]})")
                restored_count += 1
                
            except Exception as e:
                print(f"❌ 恢复用户 {username} 失败: {e}")
        
        current_conn.commit()
        
        # 最终统计
        print(f"\n=== 恢复完成 ===")
        print(f"成功恢复 {restored_count} 个用户")
        
        # 显示最终用户列表
        current_cursor.execute('SELECT username, email, is_admin FROM users ORDER BY is_admin DESC, username')
        all_users = current_cursor.fetchall()
        
        print(f"\n=== 最终用户列表 ({len(all_users)}个) ===")
        for user in all_users:
            user_type = "👑 管理员" if user[2] else "👤 普通用户"
            print(f"  {user_type}: {user[0]} ({user[1]})")
        
        backup_conn.close()
        current_conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

if __name__ == '__main__':
    restore_all_users()
