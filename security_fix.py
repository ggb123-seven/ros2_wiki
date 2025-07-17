#!/usr/bin/env python3
"""
安全修复工具 - 生成强密码和环境变量配置
米醋电子工作室 - SuperClaude安全加固
"""

import os
import secrets
import string
from werkzeug.security import generate_password_hash

class SecurityPasswordGenerator:
    """安全密码生成器"""
    
    @staticmethod
    def generate_strong_password(length=16):
        """生成强密码"""
        # 包含大小写字母、数字、特殊字符
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        # 确保包含所有字符类型
        while not (any(c.islower() for c in password) and 
                  any(c.isupper() for c in password) and
                  any(c.isdigit() for c in password) and
                  any(c in "!@#$%^&*" for c in password)):
            password = ''.join(secrets.choice(chars) for _ in range(length))
        
        return password
    
    @staticmethod
    def generate_secret_key():
        """生成Flask Secret Key"""
        return secrets.token_hex(32)
    
    @staticmethod
    def create_env_file():
        """创建安全的环境变量文件"""
        admin_password = SecurityPasswordGenerator.generate_strong_password()
        secret_key = SecurityPasswordGenerator.generate_secret_key()
        
        env_content = f"""# ROS2 Wiki 安全配置 - 米醋电子工作室
# 生成时间: {os.environ.get('DATE', 'auto-generated')}

# Flask应用配置
SECRET_KEY={secret_key}
FLASK_ENV=production

# 管理员账户配置
ADMIN_USERNAME=admin
ADMIN_PASSWORD={admin_password}

# 数据库配置
DATABASE_URL=sqlite:///ros2_wiki.db

# 安全配置
CSRF_ENABLED=True
REQUIRE_SPECIAL_CHARS=True
MIN_PASSWORD_LENGTH=12

# 会话配置
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# 日志配置
LOG_LEVEL=INFO
"""
        
        return env_content, admin_password

def main():
    """主执行函数"""
    print("SuperClaude安全修复工具启动...")
    
    # 生成安全配置
    env_content, admin_password = SecurityPasswordGenerator.create_env_file()
    
    # 保存到.env文件
    with open('F:/ros2_wiki/.env.production', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("安全配置文件已生成: .env.production")
    print(f"新管理员密码: {admin_password}")
    print("请立即保存密码到安全位置！")
    
    # 生成密码哈希用于数据库
    password_hash = generate_password_hash(admin_password)
    print(f"密码哈希: {password_hash}")
    
    return admin_password, password_hash

if __name__ == "__main__":
    main()