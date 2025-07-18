#!/usr/bin/env python3
"""
Render平台快速部署设置脚本
米醋电子工作室
"""

import os
import json
import subprocess
import sys

class RenderQuickSetup:
    """Render快速部署设置"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.setup_steps = []
    
    def log_step(self, step, status="OK"):
        """记录设置步骤"""
        message = f"[{status}] {step}"
        print(message)
        self.setup_steps.append(message)
    
    def check_render_files(self):
        """检查Render所需文件"""
        print("检查Render部署文件...")
        
        required_files = {
            'render.yaml': 'Render配置文件',
            'requirements_render.txt': 'Python依赖文件',
            'runtime.txt': 'Python版本文件',
            'app_render.py': 'Render优化应用',
            'cloud_init_db.py': '数据库初始化脚本',
        }
        
        all_present = True
        for filename, description in required_files.items():
            filepath = os.path.join(self.project_root, filename)
            if os.path.exists(filepath):
                self.log_step(f"{description}: 存在")
            else:
                self.log_step(f"{description}: 缺失", "ERROR")
                all_present = False
        
        return all_present
    
    def verify_git_status(self):
        """验证Git状态"""
        print("检查Git状态...")
        
        try:
            # 检查是否在Git仓库中
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                self.log_step("Git仓库: 未初始化", "ERROR")
                return False
            
            # 检查是否有未提交的更改
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.stdout.strip():
                self.log_step("Git状态: 有未提交更改", "WARN")
                return False
            
            # 检查远程仓库
            result = subprocess.run(['git', 'remote', '-v'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if 'github.com' in result.stdout:
                self.log_step("Git远程仓库: 已配置GitHub")
                return True
            else:
                self.log_step("Git远程仓库: 未配置GitHub", "ERROR")
                return False
                
        except FileNotFoundError:
            self.log_step("Git: 未安装", "ERROR")
            return False
    
    def generate_render_instructions(self):
        """生成Render部署指令"""
        print("生成Render部署指令...")
        
        instructions = """
# Render平台部署指令

## 1. 登录Render Dashboard
访问: https://dashboard.render.com
使用GitHub账户登录

## 2. 创建Web Service
1. 点击 "New" -> "Web Service"
2. 连接GitHub仓库: ggb123-seven/ros2_wiki
3. 选择分支: main

## 3. 配置Web Service
Name: ros2-wiki-enterprise
Environment: Python 3
Region: Oregon (US West)
Branch: main
Root Directory: (留空)

Build Command:
pip install -r requirements_render.txt
python cloud_init_db.py

Start Command:
gunicorn app_render:app --bind=0.0.0.0:$PORT --workers=2 --timeout=60

## 4. 创建PostgreSQL数据库
1. 点击 "New" -> "PostgreSQL"
2. 配置:
   - Database Name: ros2-wiki-db
   - Database: ros2_wiki
   - User: ros2_wiki_user
   - Region: Oregon (US West)
   - Plan: Starter (Free)

## 5. 配置环境变量
在Web Service中添加以下环境变量:

SECRET_KEY=3092b9fbcd9523417c2871c8d3b5410cca586856627bc323f4054c5f8f4297f4
DATABASE_URL=[从PostgreSQL服务自动连接]
FLASK_ENV=production
RENDER=true
MIN_PASSWORD_LENGTH=12
REQUIRE_SPECIAL_CHARS=True
ADMIN_USERNAME=admin
ADMIN_EMAIL=seventee_0611@qq.com
ADMIN_PASSWORD=IlukRJovZ05Tyx$b
AUTO_CREATE_ADMIN=true
CSRF_ENABLED=True
SESSION_COOKIE_SECURE=True

## 6. 部署
点击 "Create Web Service" 开始部署
等待5-10分钟完成部署

## 7. 测试
部署完成后，使用以下命令测试:
python test_render_deployment.py https://your-app.onrender.com
"""
        
        with open(os.path.join(self.project_root, 'RENDER_DEPLOY_INSTRUCTIONS.md'), 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        self.log_step("部署指令已生成: RENDER_DEPLOY_INSTRUCTIONS.md")
        return True
    
    def create_env_template(self):
        """创建环境变量模板"""
        print("创建环境变量模板...")
        
        env_template = """# Render平台环境变量配置模板
# 复制以下内容到Render Dashboard的环境变量设置中

SECRET_KEY=3092b9fbcd9523417c2871c8d3b5410cca586856627bc323f4054c5f8f4297f4
DATABASE_URL=[从PostgreSQL服务自动获取]
FLASK_ENV=production
RENDER=true
MIN_PASSWORD_LENGTH=12
REQUIRE_SPECIAL_CHARS=True
ADMIN_USERNAME=admin
ADMIN_EMAIL=seventee_0611@qq.com
ADMIN_PASSWORD=IlukRJovZ05Tyx$b
AUTO_CREATE_ADMIN=true
CSRF_ENABLED=True
SESSION_COOKIE_SECURE=True

# 可选的高级配置
# REDIS_URL=[如果使用Redis缓存]
# SENTRY_DSN=[如果使用Sentry错误监控]
# GOOGLE_CLIENT_ID=[如果使用Google OAuth]
# GOOGLE_CLIENT_SECRET=[如果使用Google OAuth]
# GITHUB_CLIENT_ID=[如果使用GitHub OAuth]
# GITHUB_CLIENT_SECRET=[如果使用GitHub OAuth]
"""
        
        with open(os.path.join(self.project_root, 'render_env_template.txt'), 'w', encoding='utf-8') as f:
            f.write(env_template)
        
        self.log_step("环境变量模板已创建: render_env_template.txt")
        return True
    
    def verify_configuration(self):
        """验证配置"""
        print("验证配置...")
        
        # 检查render.yaml
        render_yaml_path = os.path.join(self.project_root, 'render.yaml')
        if os.path.exists(render_yaml_path):
            with open(render_yaml_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'app_render:app' in content:
                    self.log_step("render.yaml: 配置正确")
                else:
                    self.log_step("render.yaml: 配置错误", "ERROR")
                    return False
        
        # 检查requirements_render.txt
        req_path = os.path.join(self.project_root, 'requirements_render.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'Flask' in content and 'gunicorn' in content:
                    self.log_step("requirements_render.txt: 配置正确")
                else:
                    self.log_step("requirements_render.txt: 配置错误", "ERROR")
                    return False
        
        # 检查runtime.txt
        runtime_path = os.path.join(self.project_root, 'runtime.txt')
        if os.path.exists(runtime_path):
            with open(runtime_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content == 'python-3.13.5':
                    self.log_step("runtime.txt: 配置正确")
                else:
                    self.log_step("runtime.txt: 配置错误", "ERROR")
                    return False
        
        return True
    
    def run_setup(self):
        """运行完整设置"""
        print("Render平台快速部署设置")
        print("=" * 50)
        
        steps = [
            ("检查部署文件", self.check_render_files),
            ("验证Git状态", self.verify_git_status),
            ("验证配置", self.verify_configuration),
            ("生成部署指令", self.generate_render_instructions),
            ("创建环境变量模板", self.create_env_template),
        ]
        
        success_count = 0
        for step_name, step_func in steps:
            print(f"\n正在执行 {step_name}...")
            try:
                if step_func():
                    success_count += 1
                else:
                    print(f"错误: {step_name}失败")
            except Exception as e:
                print(f"错误: {step_name}发生异常: {str(e)}")
        
        print("\n" + "=" * 50)
        print(f"设置完成: {success_count}/{len(steps)} 步骤成功")
        
        if success_count == len(steps):
            print("所有设置步骤完成！")
            print("\n下一步:")
            print("1. 查看 RENDER_DEPLOY_INSTRUCTIONS.md 了解详细部署步骤")
            print("2. 访问 https://dashboard.render.com 开始部署")
            print("3. 部署完成后运行测试:")
            print("   python test_render_deployment.py https://your-app.onrender.com")
            return True
        else:
            print("警告: 部分设置步骤失败，请检查上述错误信息")
            return False

def main():
    """主函数"""
    setup = RenderQuickSetup()
    
    try:
        if setup.run_setup():
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n警告: 设置被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: 设置过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()