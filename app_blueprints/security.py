# 安全验证和输入保护模块

import re
import html
from werkzeug.security import check_password_hash
from flask import request, abort
from functools import wraps
import os

# 条件导入bleach
try:
    import bleach
    HAS_BLEACH = True
except ImportError:
    HAS_BLEACH = False

# 密码强度验证
class PasswordValidator:
    """密码安全验证器"""
    
    @staticmethod
    def validate_password(password):
        """
        验证密码强度
        要求：至少8位，包含大小写字母、数字、特殊字符
        """
        min_length = int(os.environ.get('MIN_PASSWORD_LENGTH', 8))
        require_special = os.environ.get('REQUIRE_SPECIAL_CHARS', 'True').lower() == 'true'
        
        errors = []
        
        # 长度检查
        if len(password) < min_length:
            errors.append(f"密码长度至少需要{min_length}位")
        
        # 复杂度检查
        if not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")
        
        if not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")
        
        if not re.search(r'\d', password):
            errors.append("密码必须包含数字")
        
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")
        
        # 常见弱密码检查（完整匹配）
        weak_passwords = [
            '123456', '123456789', 'password', 'admin', 'qwerty', 
            'abc123', '111111', 'welcome', 'password123', 'admin123'
        ]
        
        if password.lower() in weak_passwords:
            errors.append("密码不能使用常见弱密码")
        
        return len(errors) == 0, errors

# 输入验证和清理
class InputValidator:
    """输入验证和清理工具"""
    
    # 允许的HTML标签（用于文档内容）
    ALLOWED_TAGS = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'br', 'strong', 'em', 'u', 'strike',
        'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
        'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ]
    
    # 允许的HTML属性
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'table': ['class'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan']
    }
    
    @staticmethod
    def sanitize_html(content, allow_tags=True):
        """
        清理HTML内容，防止XSS攻击
        """
        if not content:
            return ""
        
        if allow_tags and HAS_BLEACH:
            # 允许安全的HTML标签（需要bleach模块）
            return bleach.clean(
                content,
                tags=InputValidator.ALLOWED_TAGS,
                attributes=InputValidator.ALLOWED_ATTRIBUTES,
                strip=True
            )
        else:
            # 完全转义HTML（回退方案）
            return html.escape(content)
    
    @staticmethod
    def validate_username(username):
        """验证用户名格式"""
        if not username:
            return False, "用户名不能为空"
        
        if len(username) < 3 or len(username) > 20:
            return False, "用户名长度必须在3-20个字符之间"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "用户名只能包含字母、数字和下划线"
        
        # 保留用户名检查
        reserved_names = ['admin', 'root', 'system', 'api', 'www']
        if username.lower() in reserved_names:
            return False, "该用户名为系统保留，请选择其他用户名"
        
        return True, ""
    
    @staticmethod
    def validate_email(email):
        """验证邮箱格式"""
        if not email:
            return False, "邮箱不能为空"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "邮箱格式不正确"
        
        return True, ""
    
    @staticmethod
    def validate_content_length(content, max_length=10000):
        """验证内容长度"""
        if not content:
            return False, "内容不能为空"
        
        if len(content) > max_length:
            return False, f"内容长度不能超过{max_length}个字符"
        
        return True, ""

# 安全装饰器
def rate_limit(max_requests=5, window=60):
    """
    简单的请求限制装饰器
    max_requests: 时间窗口内最大请求数
    window: 时间窗口（秒）
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里可以实现更复杂的速率限制逻辑
            # 简单示例：检查请求频率
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # 在实际应用中，应该使用Redis或内存缓存来存储请求计数
            # 这里只是一个示例框架
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def validate_csrf_token(f):
    """CSRF令牌验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            csrf_enabled = os.environ.get('CSRF_ENABLED', 'True').lower() == 'true'
            if csrf_enabled:
                # 在实际应用中，应该验证CSRF令牌
                # 这里只是框架示例
                pass
        return f(*args, **kwargs)
    return decorated_function

# SQL注入防护
class DatabaseSecurity:
    """数据库安全工具"""
    
    @staticmethod
    def escape_sql_like(query):
        """转义SQL LIKE查询中的特殊字符"""
        return query.replace('%', '\\%').replace('_', '\\_')
    
    @staticmethod
    def validate_sql_params(params):
        """验证SQL参数安全性"""
        if isinstance(params, dict):
            for key, value in params.items():
                if isinstance(value, str) and any(keyword in value.lower() for keyword in 
                    ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']):
                    raise ValueError(f"检测到潜在的SQL注入尝试: {key}")
        return True

# 文件上传安全
class FileUploadSecurity:
    """文件上传安全验证"""
    
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'md'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    @staticmethod
    def allowed_file(filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileUploadSecurity.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_size(file_size):
        """验证文件大小"""
        return file_size <= FileUploadSecurity.MAX_FILE_SIZE
    
    @staticmethod
    def sanitize_filename(filename):
        """清理文件名，防止目录遍历攻击"""
        import os
        # 移除路径分隔符
        filename = os.path.basename(filename)
        # 移除危险字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename