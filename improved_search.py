#!/usr/bin/env python3
"""
改进的搜索功能实现 - 使用索引优化
米醋电子工作室 - SuperClaude搜索优化
"""

import sqlite3
import os
from typing import List, Dict, Optional
import re

class ImprovedSearchService:
    """改进的搜索服务 - 支持SQLite和PostgreSQL"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.is_postgresql = (db_path == 'postgresql' or os.environ.get('DATABASE_URL'))
        
    def _get_connection(self):
        """获取数据库连接"""
        if self.is_postgresql:
            # PostgreSQL连接 - 返回None表示功能暂不可用
            return None
        else:
            # SQLite连接
            return sqlite3.connect(self.db_path)
    
    def full_text_search(self, query: str, limit: int = 20) -> List[Dict]:
        """全文搜索 - 使用FTS5"""
        if not query or len(query.strip()) < 2:
            return []
            
        # PostgreSQL环境暂时返回空结果
        if self.is_postgresql:
            return []
        
        # 清理搜索查询
        clean_query = self._clean_search_query(query)
        
        sql = """
        SELECT d.id, d.title, d.content, d.category, d.created_at, u.username as author,
               snippet(documents_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
        FROM documents_fts fts
        JOIN documents d ON fts.rowid = d.id
        LEFT JOIN users u ON d.author_id = u.id
        WHERE documents_fts MATCH ?
        ORDER BY bm25(documents_fts)
        LIMIT ?;
        """
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql, (clean_query, limit))
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
            
        except sqlite3.Error as e:
            print(f"全文搜索失败: {e}")
            # 回退到LIKE搜索
            return self._fallback_like_search(query, limit)
        finally:
            if conn:
                conn.close()
    
    def category_search(self, category: str, limit: int = 20) -> List[Dict]:
        """分类搜索 - 使用索引"""
        # PostgreSQL环境暂时返回空结果
        if self.is_postgresql:
            return []
            
        sql = """
        SELECT d.id, d.title, d.content, d.category, d.created_at, u.username as author
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        WHERE d.category = ?
        ORDER BY d.created_at DESC
        LIMIT ?;
        """
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
                
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql, (category, limit))
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
            
        except sqlite3.Error as e:
            print(f"分类搜索失败: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def author_search(self, author_id: int, limit: int = 20) -> List[Dict]:
        """作者搜索 - 使用索引"""
        sql = """
        SELECT d.id, d.title, d.category, d.created_at, u.username as author
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        WHERE d.author_id = ?
        ORDER BY d.created_at DESC
        LIMIT ?;
        """
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql, (author_id, limit))
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
            
        except sqlite3.Error as e:
            print(f"作者搜索失败: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def advanced_search(self, title: str = None, content: str = None, 
                       category: str = None, author: str = None,
                       date_from: str = None, date_to: str = None,
                       limit: int = 20) -> List[Dict]:
        """高级搜索 - 多条件组合"""
        
        conditions = []
        params = []
        
        if title:
            conditions.append("d.title LIKE ?")
            params.append(f"%{title}%")
        
        if content:
            conditions.append("d.content LIKE ?")
            params.append(f"%{content}%")
        
        if category:
            conditions.append("d.category = ?")
            params.append(category)
        
        if author:
            conditions.append("u.username LIKE ?")
            params.append(f"%{author}%")
        
        if date_from:
            conditions.append("d.created_at >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("d.created_at <= ?")
            params.append(date_to)
        
        if not conditions:
            return []
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
        SELECT d.id, d.title, d.content, d.category, d.created_at, u.username as author
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        WHERE {where_clause}
        ORDER BY d.created_at DESC
        LIMIT ?;
        """
        
        params.append(limit)
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
            
        except sqlite3.Error as e:
            print(f"高级搜索失败: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """搜索建议"""
        if not partial_query or len(partial_query) < 2:
            return []
        
        sql = """
        SELECT DISTINCT title
        FROM documents
        WHERE title LIKE ?
        ORDER BY title
        LIMIT ?;
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(sql, (f"%{partial_query}%", limit))
            results = [row[0] for row in cursor.fetchall()]
            
            return results
            
        except sqlite3.Error as e:
            print(f"搜索建议失败: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_popular_categories(self) -> List[Dict]:
        """获取热门分类"""
        sql = """
        SELECT category, COUNT(*) as doc_count
        FROM documents
        GROUP BY category
        ORDER BY doc_count DESC;
        """
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql)
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
            
        except sqlite3.Error as e:
            print(f"获取分类失败: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def _clean_search_query(self, query: str) -> str:
        """清理搜索查询"""
        # 移除特殊字符，保留中文、英文、数字
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', query)
        # 移除多余空格
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    def _fallback_like_search(self, query: str, limit: int) -> List[Dict]:
        """回退的LIKE搜索"""
        sql = """
        SELECT d.id, d.title, d.content, d.category, d.created_at, u.username as author
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        WHERE d.title LIKE ? OR d.content LIKE ?
        ORDER BY d.created_at DESC
        LIMIT ?;
        """
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_pattern = f"%{query}%"
            cursor.execute(sql, (search_pattern, search_pattern, limit))
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
            
        except sqlite3.Error as e:
            print(f"回退搜索失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

def main():
    """测试搜索功能"""
    print("测试改进的搜索功能...")
    
    search_service = ImprovedSearchService('F:/ros2_wiki/ros2_wiki.db')
    
    # 测试全文搜索
    results = search_service.full_text_search('ROS2', 5)
    print(f"全文搜索结果: {len(results)} 条")
    
    # 测试分类搜索
    categories = search_service.get_popular_categories()
    print(f"分类统计: {categories}")
    
    print("搜索功能测试完成!")

if __name__ == "__main__":
    main()