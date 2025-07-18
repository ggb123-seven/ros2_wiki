#!/usr/bin/env python3
"""
Redis缓存管理器
米醋电子工作室 - 性能优化模块
"""

import redis
import json
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional, Dict, List

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    """Redis缓存管理器"""
    
    def __init__(self, redis_url: str = None):
        """初始化缓存管理器"""
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379')
        self.cache_prefix = 'ros2_wiki:'
        self.default_ttl = 3600  # 1小时
        
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # 测试连接
            self.redis_client.ping()
            logger.info("✅ Redis连接成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}")
            logger.info("使用内存缓存作为fallback")
            self.redis_client = None
            self._memory_cache = {}
    
    def _get_key(self, key: str) -> str:
        """获取带前缀的缓存key"""
        return f"{self.cache_prefix}{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            if self.redis_client:
                value = self.redis_client.get(self._get_key(key))
                if value:
                    return json.loads(value)
            else:
                # 内存缓存fallback
                cache_key = self._get_key(key)
                if cache_key in self._memory_cache:
                    item = self._memory_cache[cache_key]
                    if datetime.now() < item['expires']:
                        return item['value']
                    else:
                        del self._memory_cache[cache_key]
            return default
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存值"""
        try:
            ttl = ttl or self.default_ttl
            if self.redis_client:
                serialized = json.dumps(value, ensure_ascii=False, default=str)
                return self.redis_client.setex(self._get_key(key), ttl, serialized)
            else:
                # 内存缓存fallback
                cache_key = self._get_key(key)
                self._memory_cache[cache_key] = {
                    'value': value,
                    'expires': datetime.now() + timedelta(seconds=ttl)
                }
                return True
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(self._get_key(key)))
            else:
                cache_key = self._get_key(key)
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                    return True
                return False
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(self._get_key(pattern))
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # 内存缓存模式匹配
                pattern_key = self._get_key(pattern.replace('*', ''))
                count = 0
                keys_to_delete = []
                for key in self._memory_cache.keys():
                    if pattern_key in key:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    count += 1
                return count
        except Exception as e:
            logger.error(f"模式缓存清除失败: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', '0B'),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'total_commands': info.get('total_commands_processed', 0)
                }
            else:
                return {
                    'type': 'memory',
                    'total_keys': len(self._memory_cache),
                    'size_estimate': f"{len(str(self._memory_cache))} bytes"
                }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {'type': 'unknown', 'error': str(e)}

# 全局缓存实例
cache_manager = CacheManager()

def cache_result(key_prefix: str, ttl: int = 3600):
    """缓存函数结果的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存key
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            
            cache_key = ':'.join(key_parts)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        return wrapper
    return decorator

class DocumentCache:
    """文档缓存管理器"""
    
    @staticmethod
    @cache_result('documents:list', ttl=1800)  # 30分钟
    def get_document_list(category: str = None, limit: int = 10) -> List[Dict]:
        """获取文档列表（带缓存）"""
        from app import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if category:
                cursor.execute('''
                    SELECT id, title, content, category, created_at
                    FROM documents 
                    WHERE category = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (category, limit))
            else:
                cursor.execute('''
                    SELECT id, title, content, category, created_at
                    FROM documents 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                    'category': row[3],
                    'created_at': str(row[4])
                })
            
            return documents
        finally:
            conn.close()
    
    @staticmethod
    @cache_result('documents:detail', ttl=3600)  # 1小时
    def get_document_detail(doc_id: int) -> Optional[Dict]:
        """获取文档详情（带缓存）"""
        from app import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT d.*, u.username as author_name
                FROM documents d
                LEFT JOIN users u ON d.author_id = u.id
                WHERE d.id = ?
            ''', (doc_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'author_id': row[3],
                    'category': row[4],
                    'created_at': str(row[5]),
                    'updated_at': str(row[6]),
                    'author_name': row[7] if len(row) > 7 else 'Unknown'
                }
            return None
        finally:
            conn.close()
    
    @staticmethod
    @cache_result('documents:categories', ttl=7200)  # 2小时
    def get_popular_categories() -> List[Dict]:
        """获取热门分类（带缓存）"""
        from app import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM documents
                GROUP BY category
                ORDER BY count DESC
                LIMIT 10
            ''')
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'name': row[0],
                    'count': row[1]
                })
            
            return categories
        finally:
            conn.close()
    
    @staticmethod
    def invalidate_document_cache(doc_id: int = None):
        """清除文档相关缓存"""
        patterns = [
            'documents:list*',
            'documents:categories*'
        ]
        
        if doc_id:
            patterns.append(f'documents:detail*:{doc_id}*')
        
        for pattern in patterns:
            cache_manager.clear_pattern(pattern)
        
        logger.info(f"已清除文档缓存: {patterns}")

class SearchCache:
    """搜索缓存管理器"""
    
    @staticmethod
    @cache_result('search:query', ttl=900)  # 15分钟
    def search_documents(query: str, limit: int = 20) -> List[Dict]:
        """搜索文档（带缓存）"""
        from improved_search import ImprovedSearchService
        
        search_service = ImprovedSearchService('ros2_wiki.db')
        return search_service.full_text_search(query, limit)
    
    @staticmethod
    @cache_result('search:suggestions', ttl=1800)  # 30分钟
    def get_search_suggestions(query: str, limit: int = 5) -> List[str]:
        """获取搜索建议（带缓存）"""
        from improved_search import ImprovedSearchService
        
        search_service = ImprovedSearchService('ros2_wiki.db')
        return search_service.get_search_suggestions(query, limit)

# 缓存统计API
class CacheStats:
    """缓存统计信息"""
    
    @staticmethod
    def get_cache_health() -> Dict[str, Any]:
        """获取缓存健康状况"""
        stats = cache_manager.get_stats()
        
        health_score = 100
        issues = []
        
        if stats['type'] == 'redis':
            # Redis健康检查
            if stats.get('connected_clients', 0) > 100:
                health_score -= 20
                issues.append("连接数过多")
            
            hits = stats.get('hits', 0)
            misses = stats.get('misses', 0)
            if hits + misses > 0:
                hit_rate = hits / (hits + misses) * 100
                if hit_rate < 80:
                    health_score -= 30
                    issues.append(f"命中率低: {hit_rate:.1f}%")
        
        return {
            'health_score': max(0, health_score),
            'issues': issues,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # 测试缓存功能
    print("测试缓存管理器...")
    
    # 基础测试
    cache_manager.set('test_key', {'data': 'hello world'})
    result = cache_manager.get('test_key')
    print(f"缓存测试结果: {result}")
    
    # 统计信息
    stats = cache_manager.get_stats()
    print(f"缓存统计: {stats}")
    
    # 健康检查
    health = CacheStats.get_cache_health()
    print(f"缓存健康状况: {health}")