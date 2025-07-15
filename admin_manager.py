#!/usr/bin/env python3
"""
安全的管理员账户管理系统
- 支持云端部署的可靠初始化
- 避免硬编码凭据
- 提供账户恢复机制
"""

import os
import sys
import secrets
import string
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class AdminManager:
    """管理员账户安全管理器"""
    
    def __init__(self, db_conn):
        self.conn = db_conn
        self.cursor = db_conn.cursor()
    
    def generate_secure_password(self, length=16):
        """生成安全的随机密码"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def ensure_admin_exists(self):
        """确保至少存在一个管理员账户"""
        try:
            # 检查是否已有管理员
            if self._has_admin_account():
                print("✅ 管理员账户已存在")
                return True
            
            # 从环境变量创建管理员
            admin_created = self._create_admin_from_env()
            if admin_created:
                print("✅ 从环境变量创建管理员成功")
                return True
            
            # 创建恢复令牌
            recovery_token = self._create_recovery_token()
            print(f"\n⚠️ 未找到管理员账户")
            print(f"🔑 请使用以下命令创建管理员：")
            print(f"   python admin_manager.py create --token {recovery_token}")
            
            return False
            
        except Exception as e:
            print(f"❌ 管理员检查失败: {e}")
            return False
    
    def _has_admin_account(self):
        """检查是否存在管理员账户"""
        if 'postgresql' in str(self.conn):
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
        else:
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        
        count = self.cursor.fetchone()[0]
        return count > 0
    
    def _create_admin_from_env(self):
        """从环境变量安全创建管理员"""
        admin_email = os.environ.get('INITIAL_ADMIN_EMAIL')
        if not admin_email:
            return False
        
        # 检查是否已存在
        self.cursor.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        if self.cursor.fetchone():
            return False
        
        # 生成安全密码
        temp_password = self.generate_secure_password()
        password_hash = generate_password_hash(temp_password)
        
        # 创建账户
        username = admin_email.split('@')[0]
        self.cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, created_at)
            VALUES (%s, %s, %s, TRUE, %s)
        ''', (username, admin_email, password_hash, datetime.now()))
        
        self.conn.commit()
        
        # 将密码写入安全文件（仅首次）
        with open('.admin_credentials', 'w') as f:
            f.write(f"Username: {username}\n")
            f.write(f"Email: {admin_email}\n")
            f.write(f"Temporary Password: {temp_password}\n")
            f.write(f"Created: {datetime.now()}\n")
            f.write("\n⚠️ 请立即登录并修改密码！\n")
        
        os.chmod('.admin_credentials', 0o600)  # 仅所有者可读
        
        print(f"\n🔐 管理员凭据已保存到 .admin_credentials")
        print(f"⚠️ 请立即查看并删除该文件！")
        
        return True
    
    def _create_recovery_token(self):
        """创建账户恢复令牌"""
        return secrets.token_urlsafe(32)
    
    def create_admin_interactive(self, token=None):
        """交互式创建管理员账户"""
        print("\n=== 创建管理员账户 ===")
        
        # 验证令牌（如果需要）
        if os.environ.get('REQUIRE_RECOVERY_TOKEN') == 'true' and not token:
            print("❌ 需要恢复令牌")
            return False
        
        # 获取用户输入
        username = input("用户名: ").strip()
        email = input("邮箱: ").strip()
        
        # 验证输入
        if not username or not email or '@' not in email:
            print("❌ 无效的用户名或邮箱")
            return False
        
        # 检查是否已存在
        self.cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email)
        )
        if self.cursor.fetchone():
            print("❌ 用户名或邮箱已存在")
            return False
        
        # 生成密码
        password = self.generate_secure_password()
        password_hash = generate_password_hash(password)
        
        # 创建账户
        try:
            self.cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin, created_at)
                VALUES (%s, %s, %s, TRUE, %s)
            ''', (username, email, password_hash, datetime.now()))
            
            self.conn.commit()
            
            print("\n✅ 管理员账户创建成功！")
            print(f"用户名: {username}")
            print(f"邮箱: {email}")
            print(f"临时密码: {password}")
            print("\n⚠️ 请立即登录并修改密码！")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            self.conn.rollback()
            return False
    
    def verify_admin_login(self, username, password):
        """验证管理员登录（用于调试）"""
        try:
            # 查询用户
            self.cursor.execute('''
                SELECT password_hash, is_admin 
                FROM users 
                WHERE username = %s OR email = %s
            ''', (username, username))
            
            result = self.cursor.fetchone()
            if not result:
                return False, "用户不存在"
            
            password_hash, is_admin = result
            
            # 验证密码
            if not check_password_hash(password_hash, password):
                return False, "密码错误"
            
            # 验证管理员权限
            if not is_admin:
                return False, "非管理员账户"
            
            return True, "验证成功"
            
        except Exception as e:
            return False, f"验证失败: {e}"


def get_database_connection():
    """获取数据库连接"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        # 本地开发环境
        import sqlite3
        conn = sqlite3.connect('ros2_wiki.db')
        return conn
    
    if 'postgresql' in database_url:
        import psycopg2
        from urllib.parse import urlparse
        
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn
    
    raise ValueError("不支持的数据库类型")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python admin_manager.py check    # 检查管理员账户")
        print("  python admin_manager.py create   # 创建管理员账户")
        print("  python admin_manager.py verify <username> <password>  # 验证登录")
        return
    
    command = sys.argv[1]
    
    try:
        conn = get_database_connection()
        manager = AdminManager(conn)
        
        if command == 'check':
            manager.ensure_admin_exists()
        
        elif command == 'create':
            token = sys.argv[2] if len(sys.argv) > 2 else None
            manager.create_admin_interactive(token)
        
        elif command == 'verify' and len(sys.argv) >= 4:
            username = sys.argv[2]
            password = sys.argv[3]
            success, message = manager.verify_admin_login(username, password)
            print(f"{'✅' if success else '❌'} {message}")
        
        else:
            print("❌ 无效的命令")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()