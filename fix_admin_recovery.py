#!/usr/bin/env python3
"""
修复管理员恢复问题
处理邮箱冲突并完成恢复
"""

import sqlite3

def fix_admin_recovery():
    """修复管理员恢复"""
    print("=== 修复管理员恢复问题 ===")
    
    try:
        # 连接数据库
        backup_conn = sqlite3.connect('ros2_wiki.db.backup')
        current_conn = sqlite3.connect('ros2_wiki.db')
        
        backup_cursor = backup_conn.cursor()
        current_cursor = current_conn.cursor()
        
        # 查看当前状态
        print("\n=== 当前管理员状态 ===")
        current_cursor.execute('SELECT id, username, email, is_admin FROM users')
        current_users = current_cursor.fetchall()
        
        for user in current_users:
            admin_status = "👑 管理员" if user[3] else "👤 普通用户"
            print(f"ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 状态: {admin_status}")
        
        # 恢复ros2_admin_2024，但使用不同的邮箱
        print("\n=== 恢复ros2_admin_2024管理员 ===")
        backup_cursor.execute('SELECT * FROM users WHERE username = "ros2_admin_2024"')
        ros2_admin = backup_cursor.fetchone()
        
        if ros2_admin:
            # 检查是否已存在
            current_cursor.execute('SELECT id FROM users WHERE username = "ros2_admin_2024"')
            if not current_cursor.fetchone():
                # 使用修改后的邮箱避免冲突
                new_email = "ros2_admin_2024@ros2wiki.com"
                current_cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted,
                                     blacklisted_at, blacklist_reason, last_seen, created_at)
                    VALUES (?, ?, ?, 1, 0, NULL, NULL, NULL, ?)
                ''', (ros2_admin[1], new_email, ros2_admin[3], ros2_admin[5]))
                print(f"✅ 恢复管理员: {ros2_admin[1]} (邮箱: {new_email})")
            else:
                print(f"⚠️ 管理员 {ros2_admin[1]} 已存在")
        
        current_conn.commit()
        
        # 最终验证
        print("\n=== 最终管理员列表 ===")
        current_cursor.execute('SELECT username, email, is_admin FROM users WHERE is_admin = 1')
        admins = current_cursor.fetchall()
        
        print("当前所有管理员:")
        for admin in admins:
            print(f"  👑 {admin[0]} ({admin[1]})")
        
        # 特别确认ssss用户
        current_cursor.execute('SELECT username, email, is_admin FROM users WHERE username = "ssss"')
        ssss_user = current_cursor.fetchone()
        
        if ssss_user:
            print(f"\n🎯 您的账户状态:")
            print(f"   用户名: {ssss_user[0]}")
            print(f"   邮箱: {ssss_user[1]}")
            print(f"   管理员权限: {'✅ 是' if ssss_user[2] else '❌ 否'}")
        
        backup_conn.close()
        current_conn.close()
        
        print(f"\n🎉 管理员恢复修复完成！")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

if __name__ == '__main__':
    fix_admin_recovery()
