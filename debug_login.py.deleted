#!/usr/bin/env python3
"""
调试登录问题
"""

import sqlite3
from werkzeug.security import check_password_hash

def debug_login_issue():
    """调试登录问题"""
    try:
        conn = sqlite3.connect('ros2_wiki.db')
        cursor = conn.cursor()

        print('=== 数据库字段结构 ===')
        cursor.execute('PRAGMA table_info(users)')
        columns = cursor.fetchall()
        for i, col in enumerate(columns):
            print(f'索引 {i}: {col[1]} ({col[2]})')

        print('\n=== 现有用户数据 ===')
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        
        for user in users:
            print(f'\n用户: {user[1]}')
            print(f'完整数据: {user}')
            print(f'字段映射:')
            for i, value in enumerate(user):
                print(f'  [{i}]: {value}')
            
            # 测试密码验证
            test_passwords = ['admin123', 'admin', 'password', '123456', 'user123']
            print(f'\n密码测试:')
            for pwd in test_passwords:
                try:
                    is_valid = check_password_hash(user[3], pwd)
                    if is_valid:
                        print(f'  ✅ 密码 "{pwd}" 验证成功!')
                    else:
                        print(f'  ❌ 密码 "{pwd}" 验证失败')
                except Exception as e:
                    print(f'  ❌ 密码 "{pwd}" 验证出错: {e}')

        conn.close()
        
    except Exception as e:
        print(f'调试失败: {e}')

if __name__ == '__main__':
    debug_login_issue()
