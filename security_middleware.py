#!/usr/bin/env python3
"""
安全中间件 - CSRF保护和安全头
米醋电子工作室 - SuperClaude安全加固
"""

from flask import request, session, abort, current_app
from functools import wraps
import secrets
import hashlib
import time

class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # 生成CSRF密钥
        if not app.config.get('CSRF_SECRET_KEY'):
            app.config['CSRF_SECRET_KEY'] = secrets.token_hex(32)
    
    def before_request(self):
        """请求前处理"""
        # 生成CSRF令牌
        if 'csrf_token' not in session:
            session['csrf_token'] = self.generate_csrf_token()
        
        # 检查CSRF令牌（POST/PUT/DELETE请求）
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if not self.validate_csrf_token():
                abort(403, "CSRF验证失败")
    
    def after_request(self, response):
        """请求后处理 - 添加安全头"""
        
        # 基础安全头
        security_headers = {
            # 防止XSS攻击
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            
            # 内容安全策略
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self';"
            ),
            
            # 推荐安全
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # 权限策略
            'Permissions-Policy': (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), accelerometer=()"
            )
        }
        
        # HTTPS相关头（生产环境）
        if current_app.config.get('FLASK_ENV') == 'production':
            security_headers.update({
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                'Content-Security-Policy': security_headers['Content-Security-Policy'] + " upgrade-insecure-requests;"
            })
        
        # 应用安全头
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    def generate_csrf_token(self):
        """生成CSRF令牌"""
        timestamp = str(int(time.time()))
        random_value = secrets.token_hex(16)
        
        # 创建签名
        secret_key = current_app.config.get('CSRF_SECRET_KEY', 'default-secret')
        signature_data = f"{timestamp}:{random_value}:{secret_key}"
        signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return f"{timestamp}:{random_value}:{signature}"
    
    def validate_csrf_token(self):
        """验证CSRF令牌"""
        # 从表单或头部获取令牌
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        
        if not token:
            return False
        
        # 获取会话中的令牌
        session_token = session.get('csrf_token')
        if not session_token:
            return False
        
        # 简单比较（生产环境应使用更安全的比较）
        if token != session_token:
            return False
        
        # 验证令牌格式和时效性
        return self.is_token_valid(token)
    
    def is_token_valid(self, token, max_age=3600):
        """检查令牌是否有效"""
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False
            
            timestamp_str, random_value, signature = parts
            timestamp = int(timestamp_str)
            
            # 检查时效性
            current_time = int(time.time())
            if current_time - timestamp > max_age:
                return False
            
            # 验证签名
            secret_key = current_app.config.get('CSRF_SECRET_KEY', 'default-secret')
            expected_signature_data = f"{timestamp_str}:{random_value}:{secret_key}"
            expected_signature = hashlib.sha256(expected_signature_data.encode()).hexdigest()
            
            return signature == expected_signature
            
        except (ValueError, IndexError):
            return False

def csrf_protect(f):
    """CSRF保护装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            # 验证CSRF令牌
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            session_token = session.get('csrf_token')
            
            if not token or not session_token or token != session_token:
                abort(403, "CSRF验证失败")
        
        return f(*args, **kwargs)
    return decorated_function

def get_csrf_token():
    """获取当前CSRF令牌"""
    return session.get('csrf_token', '')

# 注册到Jinja2模板
def init_csrf_template_functions(app):
    """初始化CSRF模板函数"""
    app.jinja_env.globals['csrf_token'] = get_csrf_token
    app.jinja_env.globals['csrf_protect'] = csrf_protect

class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self):
        self.requests = {}  # IP -> [timestamp, ...]
    
    def is_allowed(self, ip_address, max_requests=10, window=60):
        """检查是否允许请求"""
        current_time = time.time()
        
        # 清理过期的请求记录
        if ip_address in self.requests:
            self.requests[ip_address] = [
                timestamp for timestamp in self.requests[ip_address]
                if current_time - timestamp < window
            ]
        else:
            self.requests[ip_address] = []
        
        # 检查请求数量
        if len(self.requests[ip_address]) >= max_requests:
            return False
        
        # 记录当前请求
        self.requests[ip_address].append(current_time)
        return True

# 全局速率限制器实例
rate_limiter = RateLimiter()

def rate_limit(max_requests=10, window=60):
    """速率限制装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            if not rate_limiter.is_allowed(client_ip, max_requests, window):
                abort(429, "请求过于频繁，请稍后再试")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def setup_security_middleware(app):
    """设置安全中间件"""
    # 初始化安全中间件
    security_middleware = SecurityMiddleware(app)
    
    # 初始化CSRF模板函数
    init_csrf_template_functions(app)
    
    # 设置会话安全配置
    app.config.update(
        SESSION_COOKIE_SECURE=app.config.get('FLASK_ENV') == 'production',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax'
    )
    
    print("安全中间件初始化完成")
    
    return security_middleware