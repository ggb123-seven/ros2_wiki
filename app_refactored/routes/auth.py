"""
认证路由
米醋电子工作室 - SuperClaude重构
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User
from ..services.auth_service import AuthService
from ..validators import validate_username, validate_email, validate_password

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('login.html')
        
        user = User.get_by_username(username)
        
        if user and user.check_password(password):
            login_user(user)
            
            # 记录登录日志
            auth_service.log_user_action(user.id, 'login', request.remote_addr)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证输入
        username_valid, username_error = validate_username(username)
        if not username_valid:
            flash(username_error, 'error')
            return render_template('register.html')
        
        email_valid, email_error = validate_email(email)
        if not email_valid:
            flash(email_error, 'error')
            return render_template('register.html')
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            flash(password_error, 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')
        
        # 检查用户名和邮箱是否已存在
        if User.get_by_username(username):
            flash('用户名已存在', 'error')
            return render_template('register.html')
        
        if User.get_by_email(email):
            flash('邮箱已被注册', 'error')
            return render_template('register.html')
        
        try:
            # 创建用户
            user_id = User.create(username, email, password)
            flash('注册成功，请登录', 'success')
            
            # 记录注册日志
            auth_service.log_user_action(user_id, 'register', request.remote_addr)
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'注册失败: {str(e)}', 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    # 记录登出日志
    auth_service.log_user_action(current_user.id, 'logout', request.remote_addr)
    
    logout_user()
    flash('已安全退出', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """用户资料"""
    return render_template('profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑用户资料"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        # 验证邮箱
        email_valid, email_error = validate_email(email)
        if not email_valid:
            flash(email_error, 'error')
            return render_template('edit_profile.html', user=current_user)
        
        # 检查邮箱是否被其他用户使用
        existing_user = User.get_by_email(email)
        if existing_user and existing_user.id != current_user.id:
            flash('邮箱已被其他用户使用', 'error')
            return render_template('edit_profile.html', user=current_user)
        
        try:
            current_user.email = email
            current_user.save()
            flash('资料更新成功', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            flash(f'更新失败: {str(e)}', 'error')
    
    return render_template('edit_profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码错误', 'error')
            return render_template('change_password.html')
        
        # 验证新密码
        password_valid, password_error = validate_password(new_password)
        if not password_valid:
            flash(password_error, 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return render_template('change_password.html')
        
        try:
            current_user.set_password(new_password)
            current_user.save()
            
            # 记录密码修改日志
            auth_service.log_user_action(current_user.id, 'password_change', request.remote_addr)
            
            flash('密码修改成功', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            flash(f'密码修改失败: {str(e)}', 'error')
    
    return render_template('change_password.html')

# API路由
@auth_bp.route('/api/check-username', methods=['POST'])
def check_username():
    """检查用户名是否可用"""
    username = request.json.get('username', '').strip()
    
    username_valid, error = validate_username(username)
    if not username_valid:
        return jsonify({'available': False, 'error': error})
    
    existing_user = User.get_by_username(username)
    return jsonify({'available': existing_user is None})

@auth_bp.route('/api/check-email', methods=['POST'])
def check_email():
    """检查邮箱是否可用"""
    email = request.json.get('email', '').strip()
    
    email_valid, error = validate_email(email)
    if not email_valid:
        return jsonify({'available': False, 'error': error})
    
    existing_user = User.get_by_email(email)
    return jsonify({'available': existing_user is None})