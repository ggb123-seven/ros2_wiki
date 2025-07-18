#!/usr/bin/env python3
"""
部署修复脚本：解决Render部署中的关键问题
"""
import os
import shutil
import subprocess
import sys

def main():
    """主修复流程"""
    print("开始部署修复...")
    
    # 1. 创建备份文件
    print("创建备份和修复文件...")
    
    # 备份原始base.html
    if os.path.exists('templates/base.html'):
        shutil.copy('templates/base.html', 'templates/base_backup.html')
        print("已备份 base.html")
    
    # 2. 修复模板文件
    print("修复模板文件...")
    
    # 替换有问题的模板引用
    base_html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}ROS2 Wiki{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-robot"></i> ROS2 Wiki
            </a>
            
            <div class="navbar-nav ms-auto">
                {% if current_user and current_user.is_authenticated %}
                    <span class="navbar-text me-3">
                        <i class="fas fa-user-circle"></i> 欢迎，{{ current_user.username }}！
                    </span>
                    <a class="nav-link" href="{{ url_for('logout') }}">
                        <i class="fas fa-sign-out-alt"></i> 退出
                    </a>
                {% else %}
                    <a class="nav-link" href="{{ url_for('login') }}">
                        <i class="fas fa-sign-in-alt"></i> 登录
                    </a>
                    <a class="nav-link" href="{{ url_for('register') }}">
                        <i class="fas fa-user-plus"></i> 注册
                    </a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-info alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
    
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html_content)
    print("已修复 base.html")
    
    # 3. 创建简化的app_render.py
    print("检查 app_render.py...")
    
    if not os.path.exists('app_render.py'):
        print("app_render.py 不存在，创建基本版本...")
        
        app_render_content = '''#!/usr/bin/env python3
"""
Render平台部署版本 - 简化版
"""
import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

# 配置Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    # 简化的用户加载
    return User(user_id, "admin", "admin@example.com", True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 简化的登录验证
        if username == 'admin' and password == os.environ.get('ADMIN_PASSWORD', 'admin123'):
            user = User(1, username, 'admin@example.com', True)
            login_user(user)
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        flash('注册功能正在开发中...', 'info')
        return redirect(url_for('login'))
    
    return render_template('register.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
'''
        
        with open('app_render.py', 'w', encoding='utf-8') as f:
            f.write(app_render_content)
        print("已创建简化版 app_render.py")
    
    # 4. 创建基本模板
    print("创建基本模板...")
    
    templates_dir = 'templates'
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # 创建基本首页模板
    index_content = '''{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="jumbotron bg-light p-5 rounded">
            <h1 class="display-4">欢迎使用 ROS2 Wiki</h1>
            <p class="lead">这是一个基于Flask的ROS2知识库系统，正在Render平台上运行。</p>
            <hr class="my-4">
            <p>您可以通过登录来管理文档和用户。</p>
            <a class="btn btn-primary btn-lg" href="{{ url_for('login') }}" role="button">立即登录</a>
        </div>
    </div>
</div>
{% endblock %}'''
    
    with open(f'{templates_dir}/index.html', 'w', encoding='utf-8') as f:
        f.write(index_content)
    print("已创建 index.html")
    
    # 创建登录页面模板
    login_content = '''{% extends "base.html" %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4>用户登录</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">用户名</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">密码</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">登录</button>
                    <a href="{{ url_for('register') }}" class="btn btn-link">注册账户</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    with open(f'{templates_dir}/login.html', 'w', encoding='utf-8') as f:
        f.write(login_content)
    print("已创建 login.html")
    
    # 创建注册页面模板
    register_content = '''{% extends "base.html" %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4>用户注册</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">用户名</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="email" class="form-label">邮箱</label>
                        <input type="email" class="form-control" id="email" name="email" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">密码</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">注册</button>
                    <a href="{{ url_for('login') }}" class="btn btn-link">已有账户？登录</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    with open(f'{templates_dir}/register.html', 'w', encoding='utf-8') as f:
        f.write(register_content)
    print("已创建 register.html")
    
    print("部署修复完成！")
    print("\n修复内容:")
    print("1. 修复了 base.html 中的路由错误")
    print("2. 创建了简化的 app_render.py")
    print("3. 创建了基本的HTML模板")
    print("4. 移除了不存在的路由引用")
    print("\n现在可以重新部署到Render平台")

if __name__ == '__main__':
    main()