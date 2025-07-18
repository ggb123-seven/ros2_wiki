#!/usr/bin/env python3
"""
优化模块包初始化
米醋电子工作室 - 集成所有优化功能
"""

from .cache_manager import CacheManager, DocumentCache, SearchCache, cache_result
from .advanced_security import (
    SecurityManager, 
    ThreatDetector, 
    OAuth2Provider, 
    SecurityAuditLog,
    require_security_check,
    require_api_key
)

# 全局实例
cache_manager = CacheManager()
security_manager = SecurityManager()
threat_detector = ThreatDetector()
oauth2_provider = OAuth2Provider()
audit_log = SecurityAuditLog()

__all__ = [
    'CacheManager',
    'DocumentCache',
    'SearchCache',
    'cache_result',
    'SecurityManager',
    'ThreatDetector',
    'OAuth2Provider',
    'SecurityAuditLog',
    'require_security_check',
    'require_api_key',
    'cache_manager',
    'security_manager',
    'threat_detector',
    'oauth2_provider',
    'audit_log'
]