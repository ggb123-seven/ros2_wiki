#!/usr/bin/env python3
"""
ROS2 Wiki 快速部署检查工具
检查并修复常见部署问题
"""

import os
import sys
import json
import yaml

class DeploymentChecker:
    def __init__(self):
        self.issues = []
        self.fixes = []
        
    def check_render_yaml(self):
        """检查render.yaml配置"""
        print("📋 检查render.yaml配置...")
        
        if not os.path.exists('render.yaml'):
            self.issues.append("render.yaml文件不存在")
            return False
            
        try:
            with open('render.yaml', 'r') as f:
                config = yaml.safe_load(f)
                
            # 检查关键配置
            web_service = config.get('services', [{}])[0]
            env_vars = {var['key']: var.get('value') for var in web_service.get('envVars', [])}
            
            # 检查密码配置
            admin_password = env_vars.get('ADMIN_PASSWORD', '')
            min_length = int(env_vars.get('MIN_PASSWORD_LENGTH', '8'))
            require_special = env_vars.get('REQUIRE_SPECIAL_CHARS', 'True') == 'True'
            
            print(f"   管理员密码: {'*' * len(admin_password)} ({len(admin_password)}位)")
            print(f"   最小密码长度: {min_length}")
            print(f"   需要特殊字符: {require_special}")
            
            # 验证密码是否符合要求
            if len(admin_password) < min_length:
                self.issues.append(f"密码长度({len(admin_password)})小于要求({min_length})")
                self.fixes.append("将MIN_PASSWORD_LENGTH改为较小值或使用更长的密码")
                
            if require_special and not any(c in admin_password for c in "!@#$%^&*"):
                self.issues.append("密码缺少特殊字符")
                self.fixes.append("在密码中添加特殊字符或将REQUIRE_SPECIAL_CHARS设为False")
                
            print("✅ render.yaml检查完成")
            return True
            
        except Exception as e:
            self.issues.append(f"render.yaml解析错误: {e}")
            return False
    
    def check_database_compatibility(self):
        """检查数据库兼容性"""
        print("\n🗄️ 检查数据库兼容性...")
        
        if os.path.exists('app.py'):
            with open('app.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查SQL占位符
            sqlite_placeholders = content.count('VALUES (?, ?, ?, ?)')
            postgres_placeholders = content.count('VALUES (%s, %s, %s, %s)')
            
            print(f"   SQLite占位符: {sqlite_placeholders}个")
            print(f"   PostgreSQL占位符: {postgres_placeholders}个")
            
            if sqlite_placeholders > 0 and postgres_placeholders == 0:
                self.issues.append("代码只支持SQLite，未适配PostgreSQL")
                self.fixes.append("需要添加PostgreSQL兼容性代码")
            
            print("✅ 数据库兼容性检查完成")
        else:
            self.issues.append("app.py文件不存在")
            
    def check_requirements(self):
        """检查依赖文件"""
        print("\n📦 检查依赖配置...")
        
        if not os.path.exists('requirements.txt'):
            self.issues.append("requirements.txt文件不存在")
            self.fixes.append("创建requirements.txt并添加必要的依赖")
            return False
            
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
            
        essential_packages = {
            'Flask': 'Web框架',
            'gunicorn': 'WSGI服务器',
            'psycopg2': 'PostgreSQL驱动'
        }
        
        for package, desc in essential_packages.items():
            if package.lower() not in requirements.lower():
                self.issues.append(f"缺少{desc}依赖: {package}")
                self.fixes.append(f"在requirements.txt中添加{package}")
        
        print("✅ 依赖检查完成")
        return True
    
    def generate_fix_script(self):
        """生成修复脚本"""
        if not self.issues:
            return
            
        print("\n🔧 生成修复脚本...")
        
        fix_content = """#!/usr/bin/env python3
# ROS2 Wiki 部署问题修复脚本
# 自动生成于: {}

import os

def fix_deployment():
    print("🔧 修复部署问题...")
    
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 添加具体修复代码
        if "render.yaml文件不存在" in self.issues:
            fix_content += """
    # 创建render.yaml
    if not os.path.exists('render.yaml'):
        with open('render.yaml', 'w') as f:
            f.write('''services:
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
        value: "6"
      - key: REQUIRE_SPECIAL_CHARS
        value: "False"
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
''')
        print("✅ 创建了render.yaml")
"""
        
        fix_content += """
    print("✅ 修复完成！")

if __name__ == '__main__':
    fix_deployment()
"""
        
        with open('fix_deployment.py', 'w') as f:
            f.write(fix_content)
            
        print("✅ 修复脚本已生成: fix_deployment.py")
    
    def run(self):
        """运行检查"""
        print("🔍 ROS2 Wiki 部署检查工具")
        print("="*50)
        
        # 运行各项检查
        self.check_render_yaml()
        self.check_database_compatibility()
        self.check_requirements()
        
        # 显示结果
        print("\n📊 检查结果:")
        if self.issues:
            print(f"\n❌ 发现{len(self.issues)}个问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
            
            print(f"\n💡 建议修复:")
            for i, fix in enumerate(self.fixes, 1):
                print(f"   {i}. {fix}")
                
            self.generate_fix_script()
        else:
            print("\n✅ 未发现部署问题！")
            
        print("\n📌 部署提醒:")
        print("1. 确保代码已推送到GitHub")
        print("2. 在Render.com连接GitHub仓库")
        print("3. 等待自动部署完成")
        print("4. 使用配置的管理员账号登录")

# 缺少的导入
from datetime import datetime

def main():
    """主函数"""
    checker = DeploymentChecker()
    checker.run()

if __name__ == '__main__':
    main()