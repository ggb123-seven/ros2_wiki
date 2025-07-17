#!/usr/bin/env python3
"""
安全加固版本的ROS2 Wiki应用
米醋电子工作室 - SuperClaude安全优化版本
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_required, current_user
from security_middleware import setup_security_middleware, csrf_protect, rate_limit
from improved_search import ImprovedSearchService

# 创建Flask应用
app = Flask(__name__)

# 安全配置
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', os.urandom(32).hex()),
    'CSRF_ENABLED': True,
    'SESSION_COOKIE_SECURE': os.environ.get('FLASK_ENV') == 'production',
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600,  # 1小时
})

# 初始化安全中间件
setup_security_middleware(app)

# 初始化Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录访问此页面'

# 初始化搜索服务
search_service = ImprovedSearchService('ros2_wiki.db')

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    from app_blueprints.models import User
    return User.get(user_id)

@app.route('/')
def index():
    """首页"""
    # 获取最新文档
    recent_docs = search_service.category_search('ROS2基础', 5)
    categories = search_service.get_popular_categories()
    
    return render_template('modern_index.html', 
                         recent_docs=recent_docs,
                         categories=categories)

@app.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    
    results = []
    if query:
        if category:
            # 分类搜索
            results = search_service.category_search(category, 20)
        else:
            # 全文搜索
            results = search_service.full_text_search(query, 20)
    
    return render_template('search.html', 
                         query=query, 
                         category=category,
                         results=results)

@app.route('/api/search/suggestions')
def search_suggestions():
    """搜索建议API"""
    query = request.args.get('q', '').strip()
    suggestions = search_service.get_search_suggestions(query, 5)
    
    return jsonify({'suggestions': suggestions})

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=300)  # 5次/5分钟
def login():
    """用户登录 - 带速率限制"""
    if request.method == 'POST':
        # 登录逻辑（省略具体实现）
        pass
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@csrf_protect
@rate_limit(max_requests=3, window=3600)  # 3次/小时
def register():
    """用户注册 - 带CSRF保护和速率限制"""
    if request.method == 'POST':
        # 注册逻辑（省略具体实现）
        pass
    
    return render_template('register.html')

@app.route('/admin/dashboard')
@login_required
@csrf_protect
def admin_dashboard():
    """管理员仪表板 - 需要登录和CSRF保护"""
    if not current_user.is_admin:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin_dashboard.html')

@app.route('/api/admin/users')
@login_required
@rate_limit(max_requests=20, window=60)  # API速率限制
def api_admin_users():
    """管理员用户API"""
    if not current_user.is_admin:
        return jsonify({'error': '权限不足'}), 403
    
    # 返回用户列表
    return jsonify({'users': []})

@app.errorhandler(403)
def forbidden(error):
    """403错误处理"""
    return render_template('error.html', 
                         error_code=403,
                         error_message='访问被拒绝'), 403

@app.errorhandler(429)
def too_many_requests(error):
    """429错误处理"""
    return render_template('error.html',
                         error_code=429, 
                         error_message='请求过于频繁，请稍后再试'), 429

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('error.html',
                         error_code=500,
                         error_message='服务器内部错误'), 500

if __name__ == '__main__':
    # 开发环境配置
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("🛡️ ROS2 Wiki 安全版本启动")
    print(f"🔐 CSRF保护: 已启用")
    print(f"⚡ 速率限制: 已启用") 
    print(f"🔒 安全头: 已配置")
    print(f"🚀 调试模式: {'开启' if debug_mode else '关闭'}")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=debug_mode
    )