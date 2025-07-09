# 用户权限管理模块

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import sqlite3
import os
from datetime import datetime
from app.security import (
    admin_required, InputValidator, PasswordValidator, validate_csrf_token
)

permissions_bp = Blueprint('permissions', __name__, url_prefix='/admin/users')

class UserManager:
    """用户管理器"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_all_users(self, page=1, per_page=10, search=None):
        """获取所有用户列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建查询条件
            where_clause = ""
            params = []
            
            if search:
                where_clause = "WHERE username LIKE ? OR email LIKE ?"
                params.extend([f"%{search}%", f"%{search}%"])
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM users {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * per_page
            data_sql = f"""
            SELECT id, username, email, is_admin, created_at
            FROM users {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            cursor.execute(data_sql, params + [per_page, offset])
            users = cursor.fetchall()
            
            conn.close()
            
            return {
                'users': [dict(user) for user in users],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            print(f"获取用户列表错误: {e}")
            return {'users': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}
    
    def get_user(self, user_id):
        """获取单个用户详情"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT id, username, email, is_admin, created_at
            FROM users
            WHERE id = ?
            """, [user_id])
            
            user = cursor.fetchone()
            conn.close()
            
            return dict(user) if user else None
            
        except Exception as e:
            print(f"获取用户详情错误: {e}")
            return None
    
    def create_user(self, username, email, password, is_admin=False):
        """创建新用户"""
        try:
            # 验证输入
            is_valid, error = InputValidator.validate_username(username)
            if not is_valid:
                return False, error
            
            is_valid, error = InputValidator.validate_email(email)
            if not is_valid:
                return False, error
            
            is_valid, errors = PasswordValidator.validate_password(password)
            if not is_valid:
                return False, "; ".join(errors)
            
            # 检查用户名和邮箱是否已存在
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", [username, email])
            if cursor.fetchone():
                conn.close()
                return False, "用户名或邮箱已存在"
            
            # 创建用户
            password_hash = generate_password_hash(password)
            cursor.execute("""
            INSERT INTO users (username, email, password_hash, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, [username, email, password_hash, is_admin, datetime.now()])
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return True, user_id
            
        except Exception as e:
            print(f"创建用户错误: {e}")
            return False, str(e)
    
    def update_user(self, user_id, username, email, is_admin):
        """更新用户信息"""
        try:
            # 验证输入
            is_valid, error = InputValidator.validate_username(username)
            if not is_valid:
                return False, error
            
            is_valid, error = InputValidator.validate_email(email)
            if not is_valid:
                return False, error
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户名和邮箱是否被其他用户使用
            cursor.execute("""
            SELECT id FROM users 
            WHERE (username = ? OR email = ?) AND id != ?
            """, [username, email, user_id])
            
            if cursor.fetchone():
                conn.close()
                return False, "用户名或邮箱已被其他用户使用"
            
            # 更新用户
            cursor.execute("""
            UPDATE users 
            SET username = ?, email = ?, is_admin = ?
            WHERE id = ?
            """, [username, email, is_admin, user_id])
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            return affected_rows > 0, "更新成功" if affected_rows > 0 else "用户不存在"
            
        except Exception as e:
            print(f"更新用户错误: {e}")
            return False, str(e)
    
    def change_password(self, user_id, new_password):
        """修改用户密码"""
        try:
            # 验证密码强度
            is_valid, errors = PasswordValidator.validate_password(new_password)
            if not is_valid:
                return False, "; ".join(errors)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(new_password)
            cursor.execute("""
            UPDATE users 
            SET password_hash = ?
            WHERE id = ?
            """, [password_hash, user_id])
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            return affected_rows > 0, "密码修改成功" if affected_rows > 0 else "用户不存在"
            
        except Exception as e:
            print(f"修改密码错误: {e}")
            return False, str(e)
    
    def delete_user(self, user_id):
        """删除用户"""
        try:
            # 防止删除当前登录的管理员
            if user_id == current_user.id:
                return False, "不能删除当前登录的用户"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除用户相关的评论
            cursor.execute("DELETE FROM comments WHERE user_id = ?", [user_id])
            
            # 删除用户
            cursor.execute("DELETE FROM users WHERE id = ?", [user_id])
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            return affected_rows > 0, "删除成功" if affected_rows > 0 else "用户不存在"
            
        except Exception as e:
            print(f"删除用户错误: {e}")
            return False, str(e)
    
    def toggle_admin_status(self, user_id):
        """切换用户管理员状态"""
        try:
            # 防止取消当前登录管理员的权限
            if user_id == current_user.id:
                return False, "不能修改当前登录用户的管理员权限"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取当前状态
            cursor.execute("SELECT is_admin FROM users WHERE id = ?", [user_id])
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, "用户不存在"
            
            # 切换状态
            new_status = not result[0]
            cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", [new_status, user_id])
            
            conn.commit()
            conn.close()
            
            status_text = "管理员" if new_status else "普通用户"
            return True, f"用户权限已更新为{status_text}"
            
        except Exception as e:
            print(f"切换管理员状态错误: {e}")
            return False, str(e)
    
    def get_user_statistics(self, user_id):
        """获取用户统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 用户发表的评论数
            cursor.execute("SELECT COUNT(*) FROM comments WHERE user_id = ?", [user_id])
            comment_count = cursor.fetchone()[0]
            
            # 用户创建的文档数（如果有author_id字段）
            cursor.execute("SELECT COUNT(*) FROM documents WHERE author_id = ?", [user_id])
            document_count = cursor.fetchone()[0]
            
            # 最近活动
            cursor.execute("""
            SELECT content, created_at 
            FROM comments 
            WHERE user_id = ?
            ORDER BY created_at DESC 
            LIMIT 5
            """, [user_id])
            recent_comments = cursor.fetchall()
            
            conn.close()
            
            return {
                'comment_count': comment_count,
                'document_count': document_count,
                'recent_comments': [
                    {'content': comment[0][:100] + '...' if len(comment[0]) > 100 else comment[0],
                     'created_at': comment[1]}
                    for comment in recent_comments
                ]
            }
            
        except Exception as e:
            print(f"获取用户统计错误: {e}")
            return {}

# 获取用户管理器实例
def get_user_manager():
    """获取用户管理器实例"""
    db_path = os.environ.get('SQLITE_DATABASE_URL', 'sqlite:///ros2_wiki.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]
    return UserManager(db_path)

# 路由定义
@permissions_bp.route('/')
@login_required
@admin_required
def users():
    """用户管理页面"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('search')
    
    um = get_user_manager()
    data = um.get_all_users(page, per_page, search)
    
    return render_template('admin/users.html',
                         users=data['users'],
                         pagination=data,
                         current_search=search)

@permissions_bp.route('/new')
@login_required
@admin_required
def new_user():
    """新建用户页面"""
    return render_template('admin/edit_user.html', user=None)

@permissions_bp.route('/<int:user_id>/edit')
@login_required
@admin_required
def edit_user(user_id):
    """编辑用户页面"""
    um = get_user_manager()
    user = um.get_user(user_id)
    
    if not user:
        flash('用户不存在', 'error')
        return redirect(url_for('permissions.users'))
    
    # 获取用户统计信息
    stats = um.get_user_statistics(user_id)
    user.update(stats)
    
    return render_template('admin/edit_user.html', user=user)

@permissions_bp.route('/save', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def save_user():
    """保存用户"""
    user_id = request.form.get('user_id')
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    is_admin = request.form.get('is_admin') == 'on'
    
    if not username or not email:
        flash('用户名和邮箱不能为空', 'error')
        return redirect(request.referrer or url_for('permissions.users'))
    
    um = get_user_manager()
    
    if user_id:  # 更新现有用户
        success, message = um.update_user(user_id, username, email, is_admin)
        
        # 如果需要修改密码
        if success and password:
            success, pwd_message = um.change_password(user_id, password)
            if not success:
                message += f"; 密码修改失败: {pwd_message}"
    else:  # 创建新用户
        if not password:
            flash('新用户密码不能为空', 'error')
            return redirect(request.referrer or url_for('permissions.users'))
        
        success, message = um.create_user(username, email, password, is_admin)
    
    if success:
        flash('用户保存成功', 'success')
        return redirect(url_for('permissions.users'))
    else:
        flash(f'保存失败: {message}', 'error')
        return redirect(request.referrer or url_for('permissions.users'))

@permissions_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def delete_user(user_id):
    """删除用户"""
    um = get_user_manager()
    success, message = um.delete_user(user_id)
    
    if success:
        flash('用户删除成功', 'success')
    else:
        flash(f'删除失败: {message}', 'error')
    
    return redirect(url_for('permissions.users'))

@permissions_bp.route('/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def toggle_admin(user_id):
    """切换用户管理员权限"""
    um = get_user_manager()
    success, message = um.toggle_admin_status(user_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(f'操作失败: {message}', 'error')
    
    return redirect(url_for('permissions.users'))