"""
数据库抽象层 - 支持多数据库切换
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class DatabaseAdapter(ABC):
    """数据库适配器基类"""
    
    @abstractmethod
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """执行查询"""
        pass
    
    @abstractmethod
    def execute_update(self, query: str, params: Dict = None) -> int:
        """执行更新/插入/删除"""
        pass
    
    @abstractmethod
    def get_full_text_search_query(self, table: str, columns: List[str], search_term: str) -> str:
        """获取全文搜索查询"""
        pass
    
    @abstractmethod
    def handle_json_field(self, data: Dict) -> Any:
        """处理JSON字段"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite适配器"""
    
    def __init__(self, db):
        self.db = db
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        result = self.db.session.execute(query, params or {})
        return [dict(row) for row in result]
    
    def execute_update(self, query: str, params: Dict = None) -> int:
        result = self.db.session.execute(query, params or {})
        self.db.session.commit()
        return result.rowcount
    
    def get_full_text_search_query(self, table: str, columns: List[str], search_term: str) -> str:
        """SQLite使用LIKE进行搜索"""
        conditions = [f"{col} LIKE :search_term" for col in columns]
        return f"SELECT * FROM {table} WHERE {' OR '.join(conditions)}"
    
    def handle_json_field(self, data: Dict) -> str:
        """SQLite存储JSON为字符串"""
        return json.dumps(data)


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL适配器"""
    
    def __init__(self, db):
        self.db = db
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        result = self.db.session.execute(query, params or {})
        return [dict(row) for row in result]
    
    def execute_update(self, query: str, params: Dict = None) -> int:
        result = self.db.session.execute(query, params or {})
        self.db.session.commit()
        return result.rowcount
    
    def get_full_text_search_query(self, table: str, columns: List[str], search_term: str) -> str:
        """PostgreSQL使用原生全文搜索"""
        tsvector_cols = [f"to_tsvector('simple', {col})" for col in columns]
        return f"""
        SELECT * FROM {table} 
        WHERE ({' || '.join(tsvector_cols)}) @@ to_tsquery('simple', :search_term)
        ORDER BY ts_rank(({' || '.join(tsvector_cols)}), to_tsquery('simple', :search_term)) DESC
        """
    
    def handle_json_field(self, data: Dict) -> Dict:
        """PostgreSQL原生支持JSON"""
        return data


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter
    
    def search_documents(self, search_term: str) -> List[Dict]:
        """搜索文档"""
        if not search_term:
            return []
        
        # 根据不同数据库使用不同的搜索策略
        if isinstance(self.adapter, SQLiteAdapter):
            # SQLite使用LIKE
            query = self.adapter.get_full_text_search_query(
                'documents', 
                ['title', 'content'], 
                search_term
            )
            params = {'search_term': f'%{search_term}%'}
        else:
            # PostgreSQL使用全文搜索
            query = self.adapter.get_full_text_search_query(
                'documents',
                ['title', 'content'],
                search_term
            )
            params = {'search_term': search_term}
        
        return self.adapter.execute_query(query, params)
    
    def get_document_stats(self) -> Dict:
        """获取文档统计信息"""
        # PostgreSQL可以使用窗口函数，SQLite使用子查询
        if isinstance(self.adapter, PostgreSQLAdapter):
            query = """
            SELECT 
                category,
                COUNT(*) as count,
                AVG(view_count) as avg_views,
                MAX(created_at) as latest_doc
            FROM documents
            GROUP BY category
            """
        else:
            query = """
            SELECT 
                category,
                COUNT(*) as count,
                AVG(view_count) as avg_views,
                MAX(created_at) as latest_doc
            FROM documents
            GROUP BY category
            """
        
        return self.adapter.execute_query(query)


def get_database_adapter(app) -> DatabaseAdapter:
    """根据配置获取数据库适配器"""
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    if 'postgresql' in db_url:
        from app import db
        return PostgreSQLAdapter(db)
    else:
        from app import db
        return SQLiteAdapter(db)