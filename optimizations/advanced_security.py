#!/usr/bin/env python3
"""
高级安全管理系统
米醋电子工作室 - 安全优化模块
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityManager:
    """高级安全管理器"""
    
    def __init__(self, app=None):
        self.app = app
        self.failed_attempts = {}  # IP -> {'count': int, 'last_attempt': datetime}
        self.blocked_ips = set()
        self.rate_limits = {}  # IP -> {'requests': int, 'window_start': datetime}
        
        # 安全配置
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.rate_limit_window = timedelta(minutes=1)
        self.max_requests_per_minute = 60
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        
        # 设置安全头
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            return response
    
    def get_client_ip(self) -> str:
        """获取客户端IP地址"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers['X-Forwarded-For'].split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers['X-Real-IP']
        else:
            return request.remote_addr
    
    def is_ip_blocked(self, ip: str) -> bool:
        """检查IP是否被封禁"""
        if ip in self.blocked_ips:
            return True
        
        # 检查失败尝试次数
        if ip in self.failed_attempts:
            attempt_data = self.failed_attempts[ip]
            if attempt_data['count'] >= self.max_failed_attempts:
                time_diff = datetime.now() - attempt_data['last_attempt']
                if time_diff < self.lockout_duration:
                    return True
                else:
                    # 解锁
                    del self.failed_attempts[ip]
        
        return False
    
    def record_failed_attempt(self, ip: str):
        """记录失败尝试"""
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = {'count': 0, 'last_attempt': datetime.now()}
        
        self.failed_attempts[ip]['count'] += 1
        self.failed_attempts[ip]['last_attempt'] = datetime.now()
        
        logger.warning(f"登录失败记录: IP {ip}, 失败次数: {self.failed_attempts[ip]['count']}")
    
    def check_rate_limit(self, ip: str) -> bool:
        """检查速率限制"""
        now = datetime.now()
        
        if ip not in self.rate_limits:
            self.rate_limits[ip] = {'requests': 1, 'window_start': now}
            return True
        
        rate_data = self.rate_limits[ip]
        time_diff = now - rate_data['window_start']
        
        if time_diff >= self.rate_limit_window:
            # 重置窗口
            self.rate_limits[ip] = {'requests': 1, 'window_start': now}
            return True
        
        if rate_data['requests'] >= self.max_requests_per_minute:
            return False
        
        rate_data['requests'] += 1
        return True
    
    def generate_secure_token(self, payload: Dict, expires_delta: timedelta = None) -> str:
        """生成安全Token"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        payload.update({
            'exp': datetime.utcnow() + expires_delta,
            'iat': datetime.utcnow(),
            'jti': secrets.token_hex(16)  # JWT ID
        })
        
        return jwt.encode(payload, self.app.config['SECRET_KEY'], algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证Token"""
        try:
            payload = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效Token")
            return None

class ThreatDetector:
    """威胁检测器"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'union.*select',  # SQL注入
            r'drop\s+table',  # SQL删除
            r'insert\s+into',  # SQL插入
            r'update.*set',  # SQL更新
            r'../../../',  # 路径遍历
            r'eval\s*\(',  # 代码注入
            r'exec\s*\(',  # 命令注入
        ]
        
        self.threat_scores = {}  # IP -> score
        
    def analyze_request(self, ip: str) -> Dict[str, any]:
        """分析请求威胁"""
        threat_score = 0
        threats = []
        
        # 检查请求参数
        for param_name, param_value in request.args.items():
            if self._contains_suspicious_pattern(param_value):
                threat_score += 50
                threats.append(f"可疑参数: {param_name}")
        
        # 检查POST数据
        if request.method == 'POST':
            try:
                if request.is_json:
                    data = request.get_json()
                    if data:
                        data_str = json.dumps(data)
                        if self._contains_suspicious_pattern(data_str):
                            threat_score += 60
                            threats.append("可疑JSON数据")
                else:
                    for field_name, field_value in request.form.items():
                        if self._contains_suspicious_pattern(field_value):
                            threat_score += 40
                            threats.append(f"可疑表单字段: {field_name}")
            except Exception as e:
                logger.error(f"分析POST数据失败: {e}")
        
        # 检查User-Agent
        user_agent = request.headers.get('User-Agent', '')
        if self._is_suspicious_user_agent(user_agent):
            threat_score += 30
            threats.append("可疑User-Agent")
        
        # 更新威胁分数
        if ip not in self.threat_scores:
            self.threat_scores[ip] = 0
        self.threat_scores[ip] += threat_score
        
        return {
            'threat_score': threat_score,
            'total_score': self.threat_scores[ip],
            'threats': threats,
            'risk_level': self._get_risk_level(threat_score)
        }
    
    def _contains_suspicious_pattern(self, text: str) -> bool:
        """检查文本是否包含可疑模式"""
        import re
        text_lower = text.lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """检查是否为可疑User-Agent"""
        suspicious_agents = [
            'python-requests',
            'curl',
            'wget',
            'scanner',
            'bot',
            'crawler'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(agent in user_agent_lower for agent in suspicious_agents)
    
    def _get_risk_level(self, score: int) -> str:
        """根据分数获取风险等级"""
        if score >= 100:
            return "高"
        elif score >= 50:
            return "中"
        elif score >= 20:
            return "低"
        else:
            return "正常"

class OAuth2Provider:
    """OAuth2.0集成"""
    
    def __init__(self, app=None):
        self.app = app
        self.providers = {
            'github': {
                'client_id': os.environ.get('GITHUB_CLIENT_ID'),
                'client_secret': os.environ.get('GITHUB_CLIENT_SECRET'),
                'auth_url': 'https://github.com/login/oauth/authorize',
                'token_url': 'https://github.com/login/oauth/access_token',
                'user_url': 'https://api.github.com/user'
            },
            'google': {
                'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
                'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
                'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'user_url': 'https://www.googleapis.com/oauth2/v2/userinfo'
            }
        }
    
    def get_auth_url(self, provider: str, redirect_uri: str) -> str:
        """获取OAuth认证URL"""
        if provider not in self.providers:
            raise ValueError(f"不支持的OAuth提供商: {provider}")
        
        config = self.providers[provider]
        state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': config['client_id'],
            'redirect_uri': redirect_uri,
            'scope': 'user:email' if provider == 'github' else 'openid email profile',
            'state': state,
            'response_type': 'code'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{config['auth_url']}?{query_string}"
    
    def exchange_code_for_token(self, provider: str, code: str, redirect_uri: str) -> Optional[Dict]:
        """交换授权码获取访问令牌"""
        if provider not in self.providers:
            return None
        
        config = self.providers[provider]
        
        data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        headers = {'Accept': 'application/json'}
        
        try:
            response = requests.post(config['token_url'], data=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"OAuth token exchange failed: {e}")
            return None
    
    def get_user_info(self, provider: str, access_token: str) -> Optional[Dict]:
        """获取用户信息"""
        if provider not in self.providers:
            return None
        
        config = self.providers[provider]
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get(config['user_url'], headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

# 装饰器
def require_security_check(f):
    """安全检查装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        security_manager = SecurityManager()
        threat_detector = ThreatDetector()
        
        client_ip = security_manager.get_client_ip()
        
        # 检查IP封禁
        if security_manager.is_ip_blocked(client_ip):
            logger.warning(f"封禁IP尝试访问: {client_ip}")
            return jsonify({'error': '访问被拒绝'}), 403
        
        # 检查速率限制
        if not security_manager.check_rate_limit(client_ip):
            logger.warning(f"速率限制触发: {client_ip}")
            return jsonify({'error': '请求过于频繁'}), 429
        
        # 威胁检测
        threat_analysis = threat_detector.analyze_request(client_ip)
        if threat_analysis['risk_level'] in ['高', '中']:
            logger.warning(f"威胁检测: IP {client_ip}, 风险等级: {threat_analysis['risk_level']}, 威胁: {threat_analysis['threats']}")
            
            if threat_analysis['risk_level'] == '高':
                return jsonify({'error': '请求被安全系统拒绝'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_api_key(f):
    """API密钥验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': '缺少API密钥'}), 401
        
        # 验证API密钥
        valid_keys = os.environ.get('API_KEYS', '').split(',')
        if api_key not in valid_keys:
            return jsonify({'error': '无效的API密钥'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

class SecurityAuditLog:
    """安全审计日志"""
    
    def __init__(self, log_file: str = 'security_audit.log'):
        self.log_file = log_file
        self.logger = logging.getLogger('security_audit')
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type: str, details: Dict, ip: str = None, user_id: str = None):
        """记录安全事件"""
        ip = ip or (request.remote_addr if request else 'unknown')
        
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'ip': ip,
            'user_id': user_id,
            'details': details
        }
        
        self.logger.info(json.dumps(event_data, ensure_ascii=False))
    
    def log_login_attempt(self, username: str, success: bool, ip: str = None):
        """记录登录尝试"""
        self.log_event('login_attempt', {
            'username': username,
            'success': success,
            'user_agent': request.headers.get('User-Agent', '') if request else ''
        }, ip)
    
    def log_threat_detection(self, threat_info: Dict, ip: str = None):
        """记录威胁检测"""
        self.log_event('threat_detection', threat_info, ip)
    
    def log_admin_action(self, action: str, target: str, admin_id: str, ip: str = None):
        """记录管理员操作"""
        self.log_event('admin_action', {
            'action': action,
            'target': target,
            'admin_id': admin_id
        }, ip)

# 全局实例
security_manager = SecurityManager()
threat_detector = ThreatDetector()
oauth2_provider = OAuth2Provider()
audit_log = SecurityAuditLog()

if __name__ == "__main__":
    # 测试安全功能
    print("测试安全管理系统...")
    
    # 测试威胁检测
    test_patterns = [
        "normal text",
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../etc/passwd"
    ]
    
    for pattern in test_patterns:
        detector = ThreatDetector()
        # 模拟检测（需要请求上下文）
        print(f"测试模式: {pattern}")
        contains_threat = detector._contains_suspicious_pattern(pattern)
        print(f"包含威胁: {contains_threat}")
    
    print("安全管理系统测试完成")