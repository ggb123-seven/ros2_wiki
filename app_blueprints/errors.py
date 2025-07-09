# 错误处理蓝图

from flask import Blueprint, render_template, jsonify, request, current_app
import logging
from datetime import datetime

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '资源不存在',
            'status_code': 404,
            'timestamp': datetime.now().isoformat(),
            'path': request.path
        }), 404
    
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """500错误处理"""
    # 记录错误日志
    current_app.logger.error(f'服务器错误: {error}', exc_info=True)
    
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '服务器内部错误',
            'status_code': 500,
            'timestamp': datetime.now().isoformat(),
            'path': request.path
        }), 500
    
    return render_template('errors/500.html'), 500

@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """403错误处理"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '访问被禁止',
            'status_code': 403,
            'timestamp': datetime.now().isoformat(),
            'path': request.path,
            'message': '您没有权限访问此资源'
        }), 403
    
    return render_template('errors/403.html'), 403

@errors_bp.app_errorhandler(400)
def bad_request_error(error):
    """400错误处理"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '请求格式错误',
            'status_code': 400,
            'timestamp': datetime.now().isoformat(),
            'path': request.path,
            'message': '请检查请求参数'
        }), 400
    
    return render_template('errors/400.html'), 400

@errors_bp.app_errorhandler(401)
def unauthorized_error(error):
    """401错误处理"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '未授权访问',
            'status_code': 401,
            'timestamp': datetime.now().isoformat(),
            'path': request.path,
            'message': '请先登录'
        }), 401
    
    return render_template('errors/401.html'), 401

@errors_bp.app_errorhandler(429)
def rate_limit_error(error):
    """429错误处理 - 请求频率限制"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '请求过于频繁',
            'status_code': 429,
            'timestamp': datetime.now().isoformat(),
            'path': request.path,
            'message': '请稍后再试'
        }), 429
    
    return render_template('errors/429.html'), 429

@errors_bp.app_errorhandler(413)
def payload_too_large_error(error):
    """413错误处理 - 请求体过大"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '请求体过大',
            'status_code': 413,
            'timestamp': datetime.now().isoformat(),
            'path': request.path,
            'message': '上传文件太大'
        }), 413
    
    return render_template('errors/413.html'), 413

@errors_bp.app_errorhandler(Exception)
def handle_exception(error):
    """通用异常处理"""
    # 记录详细错误信息
    current_app.logger.error(f'未处理的异常: {error}', exc_info=True)
    
    # 在生产环境中不显示详细错误信息
    if current_app.config.get('DEBUG', False):
        error_message = str(error)
    else:
        error_message = '服务器内部错误'
    
    if request.path.startswith('/api/'):
        return jsonify({
            'error': error_message,
            'status_code': 500,
            'timestamp': datetime.now().isoformat(),
            'path': request.path
        }), 500
    
    return render_template('errors/500.html', error=error_message), 500

# 数据库错误处理
@errors_bp.app_errorhandler(Exception)
def handle_database_error(error):
    """数据库错误处理"""
    if 'database' in str(error).lower() or 'sqlite' in str(error).lower():
        current_app.logger.error(f'数据库错误: {error}', exc_info=True)
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': '数据库连接错误',
                'status_code': 503,
                'timestamp': datetime.now().isoformat(),
                'path': request.path,
                'message': '服务暂时不可用，请稍后重试'
            }), 503
        
        return render_template('errors/503.html'), 503
    
    # 如果不是数据库错误，继续抛出
    raise error

# 自定义错误类
class ValidationError(Exception):
    """验证错误"""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class AuthenticationError(Exception):
    """认证错误"""
    def __init__(self, message, status_code=401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class AuthorizationError(Exception):
    """授权错误"""
    def __init__(self, message, status_code=403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

# 自定义错误处理器
@errors_bp.app_errorhandler(ValidationError)
def handle_validation_error(error):
    """处理验证错误"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '输入验证失败',
            'message': error.message,
            'status_code': error.status_code,
            'timestamp': datetime.now().isoformat(),
            'path': request.path
        }), error.status_code
    
    return render_template('errors/400.html', message=error.message), error.status_code

@errors_bp.app_errorhandler(AuthenticationError)
def handle_authentication_error(error):
    """处理认证错误"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '认证失败',
            'message': error.message,
            'status_code': error.status_code,
            'timestamp': datetime.now().isoformat(),
            'path': request.path
        }), error.status_code
    
    return render_template('errors/401.html', message=error.message), error.status_code

@errors_bp.app_errorhandler(AuthorizationError)
def handle_authorization_error(error):
    """处理授权错误"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': '权限不足',
            'message': error.message,
            'status_code': error.status_code,
            'timestamp': datetime.now().isoformat(),
            'path': request.path
        }), error.status_code
    
    return render_template('errors/403.html', message=error.message), error.status_code

# 错误日志增强
def log_error(error, extra_info=None):
    """增强的错误日志记录"""
    error_info = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'request_path': request.path if request else 'N/A',
        'request_method': request.method if request else 'N/A',
        'user_agent': request.headers.get('User-Agent', 'N/A') if request else 'N/A',
        'remote_addr': request.remote_addr if request else 'N/A'
    }
    
    if extra_info:
        error_info.update(extra_info)
    
    current_app.logger.error(f'错误详情: {error_info}', exc_info=True)