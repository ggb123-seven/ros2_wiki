#!/usr/bin/env python3
"""
优化模块集成
米醋电子工作室 - 将所有优化功能集成到主应用
"""

import os
import logging
from flask import Flask, request, jsonify
from . import (
    cache_manager,
    security_manager,
    threat_detector,
    oauth2_provider,
    audit_log,
    DocumentCache,
    SearchCache,
    require_security_check,
    require_api_key
)

logger = logging.getLogger(__name__)

def init_optimizations(app: Flask):
    """初始化所有优化功能"""
    
    # 初始化安全管理器
    security_manager.init_app(app)
    
    # 注册缓存相关API路由
    register_cache_routes(app)
    
    # 注册安全相关API路由
    register_security_routes(app)
    
    # 注册OAuth路由
    register_oauth_routes(app)
    
    # 注册系统监控路由
    register_monitoring_routes(app)
    
    logger.info("✅ 所有优化模块已成功集成")

def register_cache_routes(app: Flask):
    """注册缓存相关API路由"""
    
    @app.route('/api/cache/stats')
    @require_api_key
    def cache_stats():
        """获取缓存统计"""
        return jsonify(cache_manager.get_stats())
    
    @app.route('/api/cache/clear', methods=['POST'])
    @require_api_key
    def clear_cache():
        """清除缓存"""
        pattern = request.json.get('pattern', '*')
        count = cache_manager.clear_pattern(pattern)
        return jsonify({
            'success': True,
            'cleared_count': count,
            'pattern': pattern
        })
    
    @app.route('/api/search/suggestions')
    def search_suggestions():
        """搜索建议API"""
        query = request.args.get('q', '')
        if not query:
            return jsonify({'suggestions': []})
        
        try:
            suggestions = SearchCache.get_search_suggestions(query)
            return jsonify({'suggestions': suggestions})
        except Exception as e:
            logger.error(f"搜索建议失败: {e}")
            return jsonify({'suggestions': []})

def register_security_routes(app: Flask):
    """注册安全相关API路由"""
    
    @app.route('/api/security/status')
    @require_api_key
    def security_status():
        """获取安全状态"""
        client_ip = security_manager.get_client_ip()
        threat_analysis = threat_detector.analyze_request(client_ip)
        
        return jsonify({
            'ip': client_ip,
            'blocked': security_manager.is_ip_blocked(client_ip),
            'threat_analysis': threat_analysis,
            'timestamp': request.headers.get('X-Request-Start', 'unknown')
        })
    
    @app.route('/api/security/block', methods=['POST'])
    @require_api_key
    def block_ip():
        """封禁IP"""
        data = request.get_json()
        ip = data.get('ip')
        
        if not ip:
            return jsonify({'error': '缺少IP地址'}), 400
        
        security_manager.blocked_ips.add(ip)
        audit_log.log_event('ip_blocked', {'ip': ip, 'admin': 'api'})
        
        return jsonify({'success': True, 'blocked_ip': ip})
    
    @app.route('/api/security/audit', methods=['GET'])
    @require_api_key
    def security_audit():
        """获取安全审计日志"""
        try:
            with open('security_audit.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_logs = lines[-100:]  # 最近100条
            
            return jsonify({
                'logs': [line.strip() for line in recent_logs],
                'total_count': len(lines)
            })
        except FileNotFoundError:
            return jsonify({'logs': [], 'total_count': 0})

def register_oauth_routes(app: Flask):
    """注册OAuth路由"""
    
    @app.route('/auth/oauth/<provider>')
    def oauth_login(provider):
        """OAuth登录"""
        redirect_uri = request.url_root + f'auth/oauth/{provider}/callback'
        
        try:
            auth_url = oauth2_provider.get_auth_url(provider, redirect_uri)
            return jsonify({'auth_url': auth_url})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/auth/oauth/<provider>/callback')
    def oauth_callback(provider):
        """OAuth回调"""
        code = request.args.get('code')
        if not code:
            return jsonify({'error': '缺少授权码'}), 400
        
        redirect_uri = request.url_root + f'auth/oauth/{provider}/callback'
        
        # 交换访问令牌
        token_data = oauth2_provider.exchange_code_for_token(provider, code, redirect_uri)
        if not token_data:
            return jsonify({'error': '获取访问令牌失败'}), 400
        
        # 获取用户信息
        user_info = oauth2_provider.get_user_info(provider, token_data['access_token'])
        if not user_info:
            return jsonify({'error': '获取用户信息失败'}), 400
        
        # 记录OAuth登录
        audit_log.log_event('oauth_login', {
            'provider': provider,
            'user_info': user_info,
            'ip': security_manager.get_client_ip()
        })
        
        return jsonify({
            'success': True,
            'user_info': user_info,
            'provider': provider
        })

def register_monitoring_routes(app: Flask):
    """注册系统监控路由"""
    
    @app.route('/api/monitoring/health')
    def health_check():
        """健康检查"""
        from .cache_manager import CacheStats
        
        try:
            cache_health = CacheStats.get_cache_health()
            
            # 数据库健康检查
            db_health = check_database_health()
            
            # 系统资源检查
            system_health = check_system_health()
            
            overall_health = min(
                cache_health['health_score'],
                db_health['health_score'],
                system_health['health_score']
            )
            
            return jsonify({
                'overall_health': overall_health,
                'cache': cache_health,
                'database': db_health,
                'system': system_health,
                'status': 'healthy' if overall_health >= 80 else 'degraded' if overall_health >= 60 else 'unhealthy'
            })
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return jsonify({
                'overall_health': 0,
                'status': 'error',
                'error': str(e)
            }), 500
    
    @app.route('/api/monitoring/metrics')
    @require_api_key
    def get_metrics():
        """获取系统指标"""
        import psutil
        import time
        
        try:
            # 系统指标
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 缓存指标
            cache_stats = cache_manager.get_stats()
            
            # 威胁检测统计
            threat_stats = {
                'active_threats': len(threat_detector.threat_scores),
                'blocked_ips': len(security_manager.blocked_ips),
                'failed_attempts': len(security_manager.failed_attempts)
            }
            
            return jsonify({
                'timestamp': time.time(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'memory_available': memory.available,
                    'disk_free': disk.free
                },
                'cache': cache_stats,
                'security': threat_stats,
                'uptime': time.time() - app.config.get('START_TIME', time.time())
            })
        except Exception as e:
            logger.error(f"获取指标失败: {e}")
            return jsonify({'error': str(e)}), 500

def check_database_health():
    """检查数据库健康状态"""
    try:
        from app import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 简单查询测试
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'health_score': 100,
                'status': 'healthy',
                'issues': []
            }
        else:
            return {
                'health_score': 0,
                'status': 'unhealthy',
                'issues': ['数据库查询失败']
            }
    except Exception as e:
        return {
            'health_score': 0,
            'status': 'error',
            'issues': [f'数据库连接失败: {str(e)}']
        }

def check_system_health():
    """检查系统健康状态"""
    try:
        import psutil
        
        health_score = 100
        issues = []
        
        # 检查CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            health_score -= 20
            issues.append(f'CPU使用率过高: {cpu_percent}%')
        
        # 检查内存使用率
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            health_score -= 20
            issues.append(f'内存使用率过高: {memory.percent}%')
        
        # 检查磁盘使用率
        disk = psutil.disk_usage('/')
        if disk.percent > 85:
            health_score -= 30
            issues.append(f'磁盘使用率过高: {disk.percent}%')
        
        return {
            'health_score': max(0, health_score),
            'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 60 else 'unhealthy',
            'issues': issues
        }
    except Exception as e:
        return {
            'health_score': 0,
            'status': 'error',
            'issues': [f'系统监控失败: {str(e)}']
        }

# 中间件装饰器
def apply_security_middleware(app: Flask):
    """应用安全中间件"""
    
    @app.before_request
    def security_check():
        """在每个请求前进行安全检查"""
        
        # 跳过静态文件和健康检查
        if request.endpoint in ['static', 'health_check']:
            return
        
        client_ip = security_manager.get_client_ip()
        
        # 检查IP是否被封禁
        if security_manager.is_ip_blocked(client_ip):
            audit_log.log_event('blocked_access_attempt', {'ip': client_ip})
            return jsonify({'error': '访问被拒绝'}), 403
        
        # 检查速率限制
        if not security_manager.check_rate_limit(client_ip):
            audit_log.log_event('rate_limit_exceeded', {'ip': client_ip})
            return jsonify({'error': '请求过于频繁'}), 429
        
        # 威胁检测
        threat_analysis = threat_detector.analyze_request(client_ip)
        if threat_analysis['risk_level'] == '高':
            audit_log.log_threat_detection(threat_analysis, client_ip)
            return jsonify({'error': '请求被安全系统拒绝'}), 403
        elif threat_analysis['risk_level'] == '中':
            # 记录中等威胁但不阻止
            audit_log.log_threat_detection(threat_analysis, client_ip)

def enhance_flask_app(app: Flask):
    """增强Flask应用"""
    
    # 记录应用启动时间
    import time
    app.config['START_TIME'] = time.time()
    
    # 初始化优化模块
    init_optimizations(app)
    
    # 应用安全中间件
    apply_security_middleware(app)
    
    # 添加缓存装饰器到现有路由
    enhance_existing_routes(app)
    
    logger.info("🚀 Flask应用增强完成")

def enhance_existing_routes(app: Flask):
    """增强现有路由"""
    
    # 这里可以添加对现有路由的缓存装饰器
    # 由于需要修改现有路由，这部分在实际集成时需要在主应用中手动添加
    pass

if __name__ == "__main__":
    # 测试集成功能
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    enhance_flask_app(app)
    
    print("✅ 优化模块集成测试完成")