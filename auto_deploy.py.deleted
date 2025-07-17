#!/usr/bin/env python3
"""
ROS2 Wiki 自动化部署脚本
支持一键部署到 Render.com
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime

class AutoDeployer:
    def __init__(self):
        self.project_name = "ros2-wiki"
        self.github_repo = None
        self.render_api_key = None
        
    def check_requirements(self):
        """检查必要的工具和环境"""
        print("🔍 检查部署环境...")
        
        requirements = {
            'git': 'Git 版本控制',
            'python': 'Python 环境',
            'pip': 'Python 包管理器'
        }
        
        missing = []
        for cmd, desc in requirements.items():
            if not self.command_exists(cmd):
                missing.append(f"{desc} ({cmd})")
        
        if missing:
            print("❌ 缺少以下工具:")
            for tool in missing:
                print(f"   - {tool}")
            return False
            
        print("✅ 环境检查通过")
        return True
    
    def command_exists(self, cmd):
        """检查命令是否存在"""
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False
    
    def setup_git_repo(self):
        """设置Git仓库"""
        print("\n📦 配置Git仓库...")
        
        # 检查是否已有Git仓库
        if os.path.exists('.git'):
            print("✅ 已有Git仓库")
            
            # 获取远程仓库URL
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.github_repo = result.stdout.strip()
                print(f"   远程仓库: {self.github_repo}")
            else:
                print("⚠️  未找到远程仓库")
                self.github_repo = input("请输入GitHub仓库URL: ").strip()
                subprocess.run(['git', 'remote', 'add', 'origin', self.github_repo])
        else:
            # 初始化新仓库
            print("🆕 初始化Git仓库...")
            subprocess.run(['git', 'init'])
            
            self.github_repo = input("请输入GitHub仓库URL: ").strip()
            subprocess.run(['git', 'remote', 'add', 'origin', self.github_repo])
        
        return True
    
    def prepare_files(self):
        """准备部署文件"""
        print("\n📄 准备部署文件...")
        
        # 确保必要文件存在
        required_files = {
            'requirements.txt': self.generate_requirements(),
            'render.yaml': self.generate_render_yaml(),
            '.gitignore': self.generate_gitignore()
        }
        
        for filename, content in required_files.items():
            if not os.path.exists(filename):
                print(f"   创建 {filename}")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                print(f"   ✅ {filename} 已存在")
        
        return True
    
    def generate_requirements(self):
        """生成requirements.txt"""
        return """Flask==2.3.2
Flask-Login==0.6.2
Werkzeug==2.3.6
Markdown==3.4.4
psycopg2-binary==2.9.9
gunicorn==21.2.0
python-dotenv==1.0.0
"""
    
    def generate_render_yaml(self):
        """生成render.yaml配置"""
        return """services:
  - type: web
    name: ros2-wiki
    env: python
    region: oregon
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --host=0.0.0.0 --port=$PORT --workers=2
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: ros2-wiki-db
          property: connectionString
      - key: FLASK_ENV
        value: production
      - key: MIN_PASSWORD_LENGTH
        value: "8"
      - key: REQUIRE_SPECIAL_CHARS
        value: "True"
      - key: ADMIN_USERNAME
        value: "ssss"
      - key: ADMIN_EMAIL
        value: "seventee_0611@qq.com"
      - key: ADMIN_PASSWORD
        value: "Ssss123!"
      - key: AUTO_CREATE_ADMIN
        value: "true"

databases:
  - name: ros2-wiki-db
    databaseName: ros2_wiki
    user: ros2_wiki_user
    region: oregon
"""
    
    def generate_gitignore(self):
        """生成.gitignore"""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Temporary
*.tmp
*.bak
*.backup

# Local files
local_*
*_local.*
"""
    
    def commit_changes(self):
        """提交代码到Git"""
        print("\n💾 提交代码更改...")
        
        # 添加所有文件
        subprocess.run(['git', 'add', '-A'])
        
        # 检查是否有更改
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            # 有更改需要提交
            commit_msg = f"Auto deploy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_msg])
            print("✅ 代码已提交")
        else:
            print("ℹ️  没有需要提交的更改")
        
        # 推送到远程
        print("📤 推送到GitHub...")
        result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            # 尝试强制推送
            print("⚠️  常规推送失败，尝试强制推送...")
            subprocess.run(['git', 'push', '-u', 'origin', 'main', '--force'])
        
        print("✅ 代码已推送到GitHub")
        return True
    
    def deploy_to_render(self):
        """部署到Render"""
        print("\n🚀 部署到Render.com...")
        
        print("\n📋 部署步骤:")
        print("1. 登录 https://render.com")
        print("2. 点击 'New +' -> 'Web Service'")
        print(f"3. 连接GitHub仓库: {self.github_repo}")
        print("4. Render会自动检测到render.yaml配置")
        print("5. 点击 'Create Web Service'")
        print("\n⏳ 等待部署完成（约5-10分钟）")
        
        print("\n🔑 部署后的登录信息:")
        print("   用户名: ssss")
        print("   密码: Ssss123!")
        print("   邮箱: seventee_0611@qq.com")
        
        return True
    
    def create_deployment_script(self):
        """创建便捷部署脚本"""
        print("\n📝 创建便捷脚本...")
        
        # Windows批处理脚本
        with open('deploy.bat', 'w') as f:
            f.write("""@echo off
echo === ROS2 Wiki 快速部署 ===
git add -A
git commit -m "Update: %date% %time%"
git push origin main
echo.
echo 部署已推送到GitHub！
echo 请访问 https://render.com 查看部署状态
pause
""")
        
        # Linux/Mac Shell脚本
        with open('deploy.sh', 'w') as f:
            f.write("""#!/bin/bash
echo "=== ROS2 Wiki 快速部署 ==="
git add -A
git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main
echo ""
echo "部署已推送到GitHub！"
echo "请访问 https://render.com 查看部署状态"
""")
        
        # 设置执行权限
        if sys.platform != 'win32':
            os.chmod('deploy.sh', 0o755)
        
        print("✅ 便捷脚本已创建:")
        print("   - Windows: deploy.bat")
        print("   - Linux/Mac: deploy.sh")
        
        return True
    
    def run(self):
        """运行自动化部署"""
        print("=== ROS2 Wiki 自动化部署工具 ===")
        print("="*50)
        
        steps = [
            ("检查环境", self.check_requirements),
            ("配置Git仓库", self.setup_git_repo),
            ("准备部署文件", self.prepare_files),
            ("提交代码", self.commit_changes),
            ("部署指南", self.deploy_to_render),
            ("创建便捷脚本", self.create_deployment_script)
        ]
        
        for step_name, step_func in steps:
            print(f"\n▶️  {step_name}...")
            if not step_func():
                print(f"❌ {step_name}失败")
                return False
        
        print("\n✅ 自动化部署准备完成！")
        print("\n📌 后续步骤:")
        print("1. 访问 https://render.com 完成部署")
        print("2. 使用 deploy.bat (Windows) 或 ./deploy.sh (Linux/Mac) 快速更新")
        print("\n🎉 祝您使用愉快！")
        
        return True

def main():
    """主函数"""
    deployer = AutoDeployer()
    deployer.run()

if __name__ == '__main__':
    main()