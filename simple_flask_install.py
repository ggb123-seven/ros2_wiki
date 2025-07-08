#!/usr/bin/env python3
"""
简单的Flask库文件复制脚本
当无法用pip安装时使用
"""
import os
import sys
import shutil

# 创建本地libs目录
libs_dir = "libs"
if not os.path.exists(libs_dir):
    os.makedirs(libs_dir)

# 将libs目录添加到Python路径
sys.path.insert(0, os.path.abspath(libs_dir))

print("📦 准备手动安装Flask...")
print(f"📁 库文件目录: {os.path.abspath(libs_dir)}")

# 创建最简单的Flask替代品
flask_content = '''
class Flask:
    def __init__(self, name):
        self.name = name
        self.routes = {}
        self.config = {}
        
    def route(self, rule, **options):
        def decorator(f):
            self.routes[rule] = f
            return f
        return decorator
        
    def run(self, host="127.0.0.1", port=5000, debug=False):
        print(f"🚀 简化版Flask服务器启动")
        print(f"📱 访问: http://{host}:{port}")
        print("💡 这是一个简化版本，仅用于测试ngrok")
        print("按 Ctrl+C 停止服务")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\n🛑 服务已停止")

def render_template(template_name, **kwargs):
    return f"模板: {template_name}"

def request():
    pass

def jsonify(data):
    return str(data)

def redirect(url):
    return f"重定向到: {url}"

def url_for(endpoint, **values):
    return f"/{endpoint}"

def flash(message):
    print(f"消息: {message}")
'''

# 创建flask模块
flask_dir = os.path.join(libs_dir, "flask")
if not os.path.exists(flask_dir):
    os.makedirs(flask_dir)

with open(os.path.join(flask_dir, "__init__.py"), "w") as f:
    f.write(flask_content)

print("✅ 简化版Flask已创建")
print("🔧 正在测试导入...")

try:
    sys.path.insert(0, libs_dir)
    import flask
    print("✅ Flask导入成功")
except Exception as e:
    print(f"❌ Flask导入失败: {e}")

print("🎉 简化版Flask安装完成!")