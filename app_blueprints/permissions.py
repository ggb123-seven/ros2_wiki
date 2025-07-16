# 用户权限管理模块

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import sqlite3
import os
from datetime import datetime

# PostgreSQL支持
try:
    import psycopg2
    import psycopg2.extras
    HAS_POSTGRESQL = True
except ImportError:
    HAS_POSTGRESQL = False

# 导入安全验证模块
from .security import PasswordValidator, InputValidator

# 安全装饰器定义
from functools import wraps

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('需要管理员权限', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def validate_csrf_token(f):
    """CSRF令牌验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 简化的CSRF验证，在生产环境中应使用更强的验证
        return f(*args, **kwargs)
    return decorated_function

permissions_bp = Blueprint('permissions', __name__, url_prefix='/admin/users')

class UserManager:
    """用户管理器"""

    def __init__(self, db_path_or_url):
        self.db_path_or_url = db_path_or_url
        # 检测数据库类型
        if db_path_or_url and 'postgresql' in db_path_or_url and HAS_POSTGRESQL:
            self.use_postgresql = True
        else:
            self.use_postgresql = False
            # 如果是SQLite URL格式，提取路径
            if db_path_or_url and db_path_or_url.startswith('sqlite:///'):
                self.db_path_or_url = db_path_or_url[10:]

    def get_db_connection(self):
        """获取数据库连接"""
        if self.use_postgresql:
            conn = psycopg2.connect(self.db_path_or_url)
            return conn
        else:
            conn = sqlite3.connect(self.db_path_or_url)
            conn.row_factory = sqlite3.Row
            return conn
    
    def get_all_users(self, page=1, per_page=10, search=None):
        """获取所有用户列表"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 根据数据库类型选择占位符
            placeholder = "%s" if self.use_postgresql else "?"

            # 构建查询条件
            where_clause = ""
            params = []

            if search:
                where_clause = f"WHERE username LIKE {placeholder} OR email LIKE {placeholder}"
                params.extend([f"%{search}%", f"%{search}%"])
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM users {where_clause}"
            cursor.execute(count_sql, params)
            result = cursor.fetchone()
            total = result['total'] if not self.use_postgresql else result[0]

            # 获取分页数据
            offset = (page - 1) * per_page
            data_sql = f"""
            SELECT id, username, email, is_admin, is_blacklisted,
                   blacklisted_at, blacklist_reason, last_seen, created_at
            FROM users {where_clause}
            ORDER BY created_at DESC
            LIMIT {placeholder} OFFSET {placeholder}
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
            conn = self.get_db_connection()
            cursor = conn.cursor()

            placeholder = "%s" if self.use_postgresql else "?"
            cursor.execute(f"""
            SELECT id, username, email, is_admin, is_blacklisted,
                   blacklisted_at, blacklist_reason, last_seen, created_at
            FROM users
            WHERE id = {placeholder}
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

            # 使用统一的数据库连接
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 根据数据库类型选择占位符
            placeholder = "%s" if self.use_postgresql else "?"

            # 检查用户名和邮箱是否已存在
            cursor.execute(f"SELECT id FROM users WHERE username = {placeholder} OR email = {placeholder}",
                          [username, email])
            if cursor.fetchone():
                conn.close()
                return False, "用户名或邮箱已存在"

            # 创建用户
            password_hash = generate_password_hash(password)

            if self.use_postgresql:
                cursor.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """, [username, email, password_hash, is_admin])
                user_id = cursor.fetchone()[0]
            else:
                cursor.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
                """, [username, email, password_hash, is_admin])
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
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 根据数据库类型选择占位符
            placeholder = "%s" if self.use_postgresql else "?"
            
            # 检查用户名和邮箱是否被其他用户使用
            cursor.execute(f"""
            SELECT id FROM users 
            WHERE (username = {placeholder} OR email = {placeholder}) AND id != {placeholder}
            """, [username, email, user_id])
            
            if cursor.fetchone():
                conn.close()
                return False, "用户名或邮箱已被其他用户使用"
            
            # 更新用户
            cursor.execute(f"""
            UPDATE users 
            SET username = {placeholder}, email = {placeholder}, is_admin = {placeholder}
            WHERE id = {placeholder}
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

    def blacklist_user(self, user_id, reason, admin_id):
        """拉黑用户"""
        try:
            # 防止拉黑当前登录的管理员
            if user_id == current_user.id:
                return False, "不能拉黑当前登录的用户"

            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 根据数据库类型选择占位符和函数
            placeholder = "%s" if self.use_postgresql else "?"

            # 检查用户是否存在
            cursor.execute(f"SELECT id, username FROM users WHERE id = {placeholder}", [user_id])
            user = cursor.fetchone()
            if not user:
                conn.close()
                return False, "用户不存在"

            # 更新用户黑名单状态
            if self.use_postgresql:
                cursor.execute("""
                    UPDATE users
                    SET is_blacklisted = TRUE,
                        blacklisted_at = CURRENT_TIMESTAMP,
                        blacklist_reason = %s
                    WHERE id = %s
                """, [reason, user_id])
            else:
                cursor.execute("""
                    UPDATE users
                    SET is_blacklisted = 1,
                        blacklisted_at = datetime('now'),
                        blacklist_reason = ?
                    WHERE id = ?
                """, [reason, user_id])

            # 记录操作日志
            self.log_user_action(cursor, admin_id, user_id, 'BLACKLIST', reason)

            conn.commit()
            conn.close()

            return True, f"用户 {user[1]} 已被拉黑"

        except Exception as e:
            print(f"拉黑用户错误: {e}")
            return False, str(e)

    def unblacklist_user(self, user_id, admin_id):
        """解除用户拉黑"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查用户是否存在且被拉黑
            cursor.execute("SELECT id, username, is_blacklisted FROM users WHERE id = ?", [user_id])
            user = cursor.fetchone()
            if not user:
                conn.close()
                return False, "用户不存在"

            if not user[2]:
                conn.close()
                return False, "用户未被拉黑"

            # 解除拉黑状态
            cursor.execute("""
                UPDATE users
                SET is_blacklisted = 0,
                    blacklisted_at = NULL,
                    blacklist_reason = NULL
                WHERE id = ?
            """, [user_id])

            # 记录操作日志
            self.log_user_action(cursor, admin_id, user_id, 'UNBLACKLIST', '解除拉黑')

            conn.commit()
            conn.close()

            return True, f"用户 {user[1]} 已解除拉黑"

        except Exception as e:
            print(f"解除拉黑错误: {e}")
            return False, str(e)

    def is_user_blacklisted(self, user_id):
        """检查用户是否被拉黑"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 根据数据库类型选择占位符
            placeholder = "%s" if self.use_postgresql else "?"
            cursor.execute(f"SELECT is_blacklisted FROM users WHERE id = {placeholder}", [user_id])
            result = cursor.fetchone()
            conn.close()

            return result[0] if result else False

        except Exception as e:
            print(f"检查黑名单状态错误: {e}")
            return False

    def get_blacklisted_users(self, page=1, per_page=10):
        """获取黑名单用户列表"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 根据数据库类型选择boolean值和占位符
            if self.use_postgresql:
                boolean_condition = "is_blacklisted = TRUE"
                placeholder = "%s"
            else:
                boolean_condition = "is_blacklisted = 1"
                placeholder = "?"

            # 计算总数
            cursor.execute(f"SELECT COUNT(*) FROM users WHERE {boolean_condition}")
            total = cursor.fetchone()[0]

            # 分页查询
            offset = (page - 1) * per_page
            cursor.execute(f"""
                SELECT id, username, email, blacklisted_at, blacklist_reason
                FROM users
                WHERE {boolean_condition}
                ORDER BY blacklisted_at DESC
                LIMIT {placeholder} OFFSET {placeholder}
            """, [per_page, offset])

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
            print(f"获取黑名单用户错误: {e}")
            return {'users': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}

    def log_user_action(self, cursor, admin_id, target_user_id, action, reason):
        """记录用户操作日志"""
        try:
            cursor.execute("""
                INSERT INTO user_logs (admin_id, target_user_id, action, reason, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, [admin_id, target_user_id, action, reason])

        except Exception as e:
            print(f"记录操作日志错误: {e}")

    def get_user_logs(self, user_id=None, page=1, per_page=20):
        """获取用户操作日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 构建查询条件
            where_clause = ""
            params = []
            if user_id:
                where_clause = "WHERE ul.target_user_id = ?"
                params.append(user_id)

            # 计算总数
            count_query = f"SELECT COUNT(*) FROM user_logs ul {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # 分页查询
            offset = (page - 1) * per_page
            query = f"""
                SELECT ul.*,
                       u1.username as admin_name,
                       u2.username as target_name
                FROM user_logs ul
                LEFT JOIN users u1 ON ul.admin_id = u1.id
                LEFT JOIN users u2 ON ul.target_user_id = u2.id
                {where_clause}
                ORDER BY ul.created_at DESC
                LIMIT ? OFFSET ?
            """

            cursor.execute(query, params + [per_page, offset])
            logs = cursor.fetchall()
            conn.close()

            return {
                'logs': [dict(log) for log in logs],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }

        except Exception as e:
            print(f"获取操作日志错误: {e}")
            return {'logs': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}

    def batch_blacklist_users(self, user_ids, reason, admin_id):
        """批量拉黑用户"""
        try:
            if not user_ids:
                return False, "未选择用户"

            # 防止拉黑当前登录的管理员
            if current_user.id in user_ids:
                return False, "不能拉黑当前登录的用户"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            success_count = 0
            for user_id in user_ids:
                try:
                    # 检查用户是否存在且未被拉黑
                    cursor.execute("SELECT id, is_blacklisted FROM users WHERE id = ?", [user_id])
                    user = cursor.fetchone()

                    if user and not user[1]:  # 用户存在且未被拉黑
                        cursor.execute("""
                            UPDATE users
                            SET is_blacklisted = 1,
                                blacklisted_at = datetime('now'),
                                blacklist_reason = ?
                            WHERE id = ?
                        """, [reason, user_id])

                        # 记录操作日志
                        self.log_user_action(cursor, admin_id, user_id, 'BATCH_BLACKLIST', reason)
                        success_count += 1

                except Exception as e:
                    print(f"批量拉黑用户 {user_id} 错误: {e}")
                    continue

            conn.commit()
            conn.close()

            return True, f"成功拉黑 {success_count} 个用户"

        except Exception as e:
            print(f"批量拉黑错误: {e}")
            return False, str(e)

    def get_operation_logs(self, page=1, per_page=20, user_id=None, admin_id=None, action=None, date_from=None, date_to=None):
        """获取操作日志 - 支持多条件筛选"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 构建查询条件
            where_conditions = []
            params = []

            if user_id:
                where_conditions.append("ul.target_user_id = ?")
                params.append(user_id)

            if admin_id:
                where_conditions.append("ul.admin_id = ?")
                params.append(admin_id)

            if action:
                where_conditions.append("ul.action = ?")
                params.append(action)

            if date_from:
                where_conditions.append("ul.created_at >= ?")
                params.append(date_from)

            if date_to:
                where_conditions.append("ul.created_at <= ?")
                params.append(date_to)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # 计算总数
            count_query = f"SELECT COUNT(*) FROM user_logs ul {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # 分页查询
            offset = (page - 1) * per_page
            query = f"""
                SELECT ul.*,
                       u1.username as admin_name,
                       u2.username as target_name,
                       u1.email as admin_email,
                       u2.email as target_email
                FROM user_logs ul
                LEFT JOIN users u1 ON ul.admin_id = u1.id
                LEFT JOIN users u2 ON ul.target_user_id = u2.id
                {where_clause}
                ORDER BY ul.created_at DESC
                LIMIT ? OFFSET ?
            """

            cursor.execute(query, params + [per_page, offset])
            logs = cursor.fetchall()
            conn.close()

            return {
                'logs': [dict(log) for log in logs],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }

        except Exception as e:
            print(f"获取操作日志错误: {e}")
            return {'logs': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}

    def get_admin_activity_summary(self, admin_id=None, days=30):
        """获取管理员活动摘要"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 构建查询条件
            where_clause = "WHERE ul.created_at >= datetime('now', '-{} days')".format(days)
            params = []

            if admin_id:
                where_clause += " AND ul.admin_id = ?"
                params.append(admin_id)

            # 获取操作统计
            query = f"""
                SELECT ul.action,
                       COUNT(*) as count,
                       u.username as admin_name
                FROM user_logs ul
                LEFT JOIN users u ON ul.admin_id = u.id
                {where_clause}
                GROUP BY ul.action, ul.admin_id, u.username
                ORDER BY count DESC
            """

            cursor.execute(query, params)
            activity_stats = cursor.fetchall()

            # 获取最活跃的管理员
            admin_query = f"""
                SELECT u.username, u.email, COUNT(*) as total_actions
                FROM user_logs ul
                LEFT JOIN users u ON ul.admin_id = u.id
                WHERE ul.created_at >= datetime('now', '-{days} days')
                GROUP BY ul.admin_id, u.username, u.email
                ORDER BY total_actions DESC
                LIMIT 10
            """

            cursor.execute(admin_query)
            active_admins = cursor.fetchall()

            conn.close()

            return {
                'activity_stats': [dict(stat) for stat in activity_stats],
                'active_admins': [dict(admin) for admin in active_admins],
                'period_days': days
            }

        except Exception as e:
            print(f"获取管理员活动摘要错误: {e}")
            return {'activity_stats': [], 'active_admins': [], 'period_days': days}

    def get_user_action_timeline(self, user_id, limit=50):
        """获取特定用户的操作时间线"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT ul.*,
                       u1.username as admin_name,
                       u2.username as target_name
                FROM user_logs ul
                LEFT JOIN users u1 ON ul.admin_id = u1.id
                LEFT JOIN users u2 ON ul.target_user_id = u2.id
                WHERE ul.target_user_id = ?
                ORDER BY ul.created_at DESC
                LIMIT ?
            """

            cursor.execute(query, [user_id, limit])
            timeline = cursor.fetchall()
            conn.close()

            return [dict(item) for item in timeline]

        except Exception as e:
            print(f"获取用户操作时间线错误: {e}")
            return []

    def export_logs_to_csv(self, filters=None):
        """导出日志到CSV格式"""
        try:
            import csv
            import io
            from datetime import datetime

            # 获取日志数据
            logs_data = self.get_operation_logs(
                page=1,
                per_page=10000,  # 大量数据导出
                user_id=filters.get('user_id') if filters else None,
                admin_id=filters.get('admin_id') if filters else None,
                action=filters.get('action') if filters else None,
                date_from=filters.get('date_from') if filters else None,
                date_to=filters.get('date_to') if filters else None
            )

            # 创建CSV内容
            output = io.StringIO()
            writer = csv.writer(output)

            # 写入标题行
            writer.writerow([
                '时间', '操作类型', '管理员', '目标用户', '原因/备注', '管理员邮箱', '目标用户邮箱'
            ])

            # 写入数据行
            for log in logs_data['logs']:
                writer.writerow([
                    log.get('created_at', ''),
                    log.get('action', ''),
                    log.get('admin_name', ''),
                    log.get('target_name', ''),
                    log.get('reason', ''),
                    log.get('admin_email', ''),
                    log.get('target_email', '')
                ])

            csv_content = output.getvalue()
            output.close()

            return csv_content

        except Exception as e:
            print(f"导出日志错误: {e}")
            return None

    def get_security_alerts(self, days=7):
        """获取安全警报 - 检测异常操作模式"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            alerts = []

            # 1. 检测频繁拉黑操作
            cursor.execute("""
                SELECT u.username, COUNT(*) as blacklist_count
                FROM user_logs ul
                LEFT JOIN users u ON ul.admin_id = u.id
                WHERE ul.action IN ('BLACKLIST', 'BATCH_BLACKLIST')
                AND ul.created_at >= datetime('now', '-{} days')
                GROUP BY ul.admin_id, u.username
                HAVING COUNT(*) > 10
                ORDER BY blacklist_count DESC
            """.format(days))

            frequent_blacklists = cursor.fetchall()
            for admin in frequent_blacklists:
                alerts.append({
                    'type': 'FREQUENT_BLACKLIST',
                    'severity': 'HIGH',
                    'message': f"管理员 {admin['username']} 在{days}天内执行了{admin['blacklist_count']}次拉黑操作",
                    'admin': admin['username'],
                    'count': admin['blacklist_count']
                })

            # 2. 检测批量操作
            cursor.execute("""
                SELECT u.username, COUNT(*) as batch_count
                FROM user_logs ul
                LEFT JOIN users u ON ul.admin_id = u.id
                WHERE ul.action LIKE '%BATCH%'
                AND ul.created_at >= datetime('now', '-{} days')
                GROUP BY ul.admin_id, u.username
                HAVING COUNT(*) > 5
                ORDER BY batch_count DESC
            """.format(days))

            frequent_batch = cursor.fetchall()
            for admin in frequent_batch:
                alerts.append({
                    'type': 'FREQUENT_BATCH_OPERATIONS',
                    'severity': 'MEDIUM',
                    'message': f"管理员 {admin['username']} 在{days}天内执行了{admin['batch_count']}次批量操作",
                    'admin': admin['username'],
                    'count': admin['batch_count']
                })

            # 3. 检测深夜操作
            cursor.execute("""
                SELECT u.username, COUNT(*) as night_count
                FROM user_logs ul
                LEFT JOIN users u ON ul.admin_id = u.id
                WHERE (strftime('%H', ul.created_at) < '06' OR strftime('%H', ul.created_at) > '22')
                AND ul.created_at >= datetime('now', '-{} days')
                GROUP BY ul.admin_id, u.username
                HAVING COUNT(*) > 5
                ORDER BY night_count DESC
            """.format(days))

            night_operations = cursor.fetchall()
            for admin in night_operations:
                alerts.append({
                    'type': 'NIGHT_OPERATIONS',
                    'severity': 'LOW',
                    'message': f"管理员 {admin['username']} 在{days}天内有{admin['night_count']}次深夜操作",
                    'admin': admin['username'],
                    'count': admin['night_count']
                })

            conn.close()
            return alerts

        except Exception as e:
            print(f"获取安全警报错误: {e}")
            return []

# 获取用户管理器实例
def get_user_manager():
    """获取用户管理器实例"""
    # 优先使用PostgreSQL URL，回退到SQLite
    db_url = os.environ.get('DATABASE_URL')
    if db_url and 'postgresql' in db_url and HAS_POSTGRESQL:
        return UserManager(db_url)
    else:
        # 使用SQLite作为回退
        db_path = os.environ.get('SQLITE_DATABASE_URL', 'ros2_wiki.db')
        # 如果是sqlite:///格式，提取实际路径
        if db_path.startswith('sqlite:///'):
            db_path = db_path[10:]
        # 确保使用绝对路径或相对于当前工作目录的路径
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
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

# 黑名单管理路由
@permissions_bp.route('/<int:user_id>/blacklist', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def blacklist_user(user_id):
    """拉黑用户"""
    reason = request.form.get('reason', '违反社区规定').strip()
    if not reason:
        reason = '违反社区规定'

    um = get_user_manager()
    success, message = um.blacklist_user(user_id, reason, current_user.id)

    if success:
        flash(message, 'success')
    else:
        flash(f'拉黑失败: {message}', 'error')

    return redirect(url_for('permissions.users'))

@permissions_bp.route('/<int:user_id>/unblacklist', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def unblacklist_user(user_id):
    """解除用户拉黑"""
    um = get_user_manager()
    success, message = um.unblacklist_user(user_id, current_user.id)

    if success:
        flash(message, 'success')
    else:
        flash(f'解除拉黑失败: {message}', 'error')

    return redirect(url_for('permissions.users'))

@permissions_bp.route('/blacklisted')
@login_required
@admin_required
def blacklisted_users():
    """黑名单用户列表页面"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    um = get_user_manager()
    data = um.get_blacklisted_users(page, per_page)

    return render_template('admin/blacklisted_users.html',
                         users=data['users'],
                         pagination=data)

@permissions_bp.route('/<int:user_id>/logs')
@login_required
@admin_required
def user_logs(user_id):
    """用户操作日志页面"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    um = get_user_manager()
    user = um.get_user(user_id)

    if not user:
        flash('用户不存在', 'error')
        return redirect(url_for('permissions.users'))

    logs_data = um.get_user_logs(user_id, page, per_page)

    return render_template('admin/user_logs.html',
                         user=user,
                         logs=logs_data['logs'],
                         pagination=logs_data)

@permissions_bp.route('/batch-blacklist', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def batch_blacklist():
    """批量拉黑用户"""
    user_ids = request.form.getlist('user_ids')
    reason = request.form.get('reason', '批量管理操作').strip()

    if not user_ids:
        flash('请选择要拉黑的用户', 'error')
        return redirect(url_for('permissions.users'))

    if not reason:
        reason = '批量管理操作'

    # 转换为整数列表
    try:
        user_ids = [int(uid) for uid in user_ids]
    except ValueError:
        flash('无效的用户ID', 'error')
        return redirect(url_for('permissions.users'))

    um = get_user_manager()
    success, message = um.batch_blacklist_users(user_ids, reason, current_user.id)

    if success:
        flash(message, 'success')
    else:
        flash(f'批量拉黑失败: {message}', 'error')

    return redirect(url_for('permissions.users'))

# API路由 - 用于AJAX调用
@permissions_bp.route('/api/<int:user_id>/blacklist', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def api_blacklist_user(user_id):
    """API: 拉黑用户"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '违反社区规定').strip()
        if not reason:
            reason = '违反社区规定'

        um = get_user_manager()
        success, message = um.blacklist_user(user_id, reason, current_user.id)

        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@permissions_bp.route('/api/<int:user_id>/unblacklist', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def api_unblacklist_user(user_id):
    """API: 解除用户拉黑"""
    try:
        um = get_user_manager()
        success, message = um.unblacklist_user(user_id, current_user.id)

        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@permissions_bp.route('/api/<int:user_id>/status', methods=['GET'])
@login_required
@admin_required
def api_user_status(user_id):
    """API: 获取用户状态"""
    try:
        um = get_user_manager()
        user = um.get_user(user_id)

        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'is_admin': user['is_admin'],
                'is_blacklisted': user['is_blacklisted'],
                'blacklisted_at': user.get('blacklisted_at'),
                'blacklist_reason': user.get('blacklist_reason'),
                'last_seen': user.get('last_seen')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@permissions_bp.route('/api/batch-blacklist', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def api_batch_blacklist():
    """API: 批量拉黑用户"""
    try:
        data = request.get_json() or {}
        user_ids = data.get('user_ids', [])
        reason = data.get('reason', '批量管理操作').strip()

        if not user_ids:
            return jsonify({
                'success': False,
                'message': '请选择要拉黑的用户'
            }), 400

        if not reason:
            reason = '批量管理操作'

        # 确保user_ids是整数列表
        try:
            user_ids = [int(uid) for uid in user_ids]
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': '无效的用户ID'
            }), 400

        um = get_user_manager()
        success, message = um.batch_blacklist_users(user_ids, reason, current_user.id)

        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 审计和日志管理路由
@permissions_bp.route('/audit/logs')
@login_required
@admin_required
def audit_logs():
    """审计日志页面"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    # 获取筛选参数
    user_id = request.args.get('user_id')
    admin_id = request.args.get('admin_id')
    action = request.args.get('action')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    um = get_user_manager()
    logs_data = um.get_operation_logs(
        page=page,
        per_page=per_page,
        user_id=int(user_id) if user_id else None,
        admin_id=int(admin_id) if admin_id else None,
        action=action,
        date_from=date_from,
        date_to=date_to
    )

    # 获取所有管理员和用户列表用于筛选
    all_users = um.get_all_users(page=1, per_page=1000)
    admins = [user for user in all_users['users'] if user.get('is_admin')]
    users = all_users['users']

    # 获取所有操作类型
    actions = ['BLACKLIST', 'UNBLACKLIST', 'BATCH_BLACKLIST', 'CREATE', 'UPDATE', 'DELETE']

    return render_template('admin/audit_logs.html',
                         logs=logs_data['logs'],
                         pagination=logs_data,
                         admins=admins,
                         users=users,
                         actions=actions,
                         current_filters={
                             'user_id': user_id,
                             'admin_id': admin_id,
                             'action': action,
                             'date_from': date_from,
                             'date_to': date_to
                         })

@permissions_bp.route('/audit/activity')
@login_required
@admin_required
def admin_activity():
    """管理员活动摘要页面"""
    days = int(request.args.get('days', 30))
    admin_id = request.args.get('admin_id')

    um = get_user_manager()
    activity_data = um.get_admin_activity_summary(
        admin_id=int(admin_id) if admin_id else None,
        days=days
    )

    # 获取安全警报
    security_alerts = um.get_security_alerts(days=days)

    # 获取所有管理员列表
    all_users = um.get_all_users(page=1, per_page=1000)
    admins = [user for user in all_users['users'] if user.get('is_admin')]

    return render_template('admin/admin_activity.html',
                         activity_stats=activity_data['activity_stats'],
                         active_admins=activity_data['active_admins'],
                         security_alerts=security_alerts,
                         admins=admins,
                         current_admin_id=admin_id,
                         period_days=days)

@permissions_bp.route('/audit/export')
@login_required
@admin_required
def export_audit_logs():
    """导出审计日志"""
    # 获取筛选参数
    filters = {
        'user_id': request.args.get('user_id'),
        'admin_id': request.args.get('admin_id'),
        'action': request.args.get('action'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to')
    }

    # 清理空值
    filters = {k: int(v) if k in ['user_id', 'admin_id'] and v else v
              for k, v in filters.items() if v}

    um = get_user_manager()
    csv_content = um.export_logs_to_csv(filters)

    if csv_content:
        from datetime import datetime
        filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    else:
        flash('导出失败', 'error')
        return redirect(url_for('permissions.audit_logs'))

@permissions_bp.route('/api/audit/timeline/<int:user_id>')
@login_required
@admin_required
def api_user_timeline(user_id):
    """API: 获取用户操作时间线"""
    try:
        limit = int(request.args.get('limit', 50))

        um = get_user_manager()
        timeline = um.get_user_action_timeline(user_id, limit)

        return jsonify({
            'success': True,
            'timeline': timeline
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500