# 搜索功能模块

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
import sqlite3
import re
from app.security import InputValidator, DatabaseSecurity
import os

search_bp = Blueprint('search', __name__, url_prefix='/search')

class SearchEngine:
    """搜索引擎类"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def full_text_search(self, query, limit=20, offset=0):
        """
        全文搜索功能
        支持标题、内容、分类搜索
        """
        if not query or len(query.strip()) < 2:
            return {'results': [], 'total': 0, 'query': query}
        
        # 清理和验证搜索查询
        clean_query = InputValidator.sanitize_html(query.strip(), allow_tags=False)
        safe_query = DatabaseSecurity.escape_sql_like(clean_query)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建搜索SQL - 支持标题、内容、分类搜索
            search_sql = """
            SELECT 
                id, title, content, category, created_at,
                CASE 
                    WHEN title LIKE ? THEN 10
                    WHEN category LIKE ? THEN 5
                    WHEN content LIKE ? THEN 1
                    ELSE 0
                END as relevance_score
            FROM documents 
            WHERE title LIKE ? OR content LIKE ? OR category LIKE ?
            ORDER BY relevance_score DESC, created_at DESC
            LIMIT ? OFFSET ?
            """
            
            search_pattern = f"%{safe_query}%"
            search_params = [
                search_pattern, search_pattern, search_pattern,  # 用于计算相关性
                search_pattern, search_pattern, search_pattern,  # 用于WHERE条件
                limit, offset
            ]
            
            cursor.execute(search_sql, search_params)
            results = cursor.fetchall()
            
            # 获取总数
            count_sql = """
            SELECT COUNT(*) as total 
            FROM documents 
            WHERE title LIKE ? OR content LIKE ? OR category LIKE ?
            """
            cursor.execute(count_sql, [search_pattern, search_pattern, search_pattern])
            total = cursor.fetchone()['total']
            
            # 处理搜索结果
            formatted_results = []
            for row in results:
                # 生成摘要，高亮搜索关键词
                snippet = self._generate_snippet(row['content'], clean_query)
                highlighted_title = self._highlight_text(row['title'], clean_query)
                
                formatted_results.append({
                    'id': row['id'],
                    'title': highlighted_title,
                    'snippet': snippet,
                    'category': row['category'],
                    'created_at': row['created_at'],
                    'relevance_score': row['relevance_score']
                })
            
            conn.close()
            
            return {
                'results': formatted_results,
                'total': total,
                'query': clean_query,
                'page': offset // limit + 1,
                'per_page': limit
            }
            
        except Exception as e:
            print(f"搜索错误: {e}")
            return {'results': [], 'total': 0, 'query': query, 'error': str(e)}
    
    def _generate_snippet(self, content, query, max_length=200):
        """
        生成搜索结果摘要
        尝试包含查询关键词的上下文
        """
        if not content:
            return ""
        
        # 移除HTML标签
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        if len(clean_content) <= max_length:
            return self._highlight_text(clean_content, query)
        
        # 查找关键词在内容中的位置
        query_lower = query.lower()
        content_lower = clean_content.lower()
        
        # 寻找最佳摘要位置
        best_pos = content_lower.find(query_lower)
        if best_pos == -1:
            # 如果没找到精确匹配，返回开头部分
            snippet = clean_content[:max_length] + "..."
        else:
            # 以关键词为中心生成摘要
            start = max(0, best_pos - max_length // 3)
            end = min(len(clean_content), start + max_length)
            
            snippet = clean_content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(clean_content):
                snippet = snippet + "..."
        
        return self._highlight_text(snippet, query)
    
    def _highlight_text(self, text, query):
        """
        在文本中高亮显示搜索关键词
        """
        if not query:
            return text
        
        # 使用CSS类来高亮
        highlighted = re.sub(
            f'({re.escape(query)})',
            r'<mark class="search-highlight">\1</mark>',
            text,
            flags=re.IGNORECASE
        )
        return highlighted
    
    def get_search_suggestions(self, query, limit=5):
        """
        获取搜索建议
        基于标题和分类提供自动完成
        """
        if not query or len(query.strip()) < 2:
            return []
        
        clean_query = InputValidator.sanitize_html(query.strip(), allow_tags=False)
        safe_query = DatabaseSecurity.escape_sql_like(clean_query)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 从标题和分类中获取建议
            suggestions_sql = """
            SELECT DISTINCT title as suggestion, 'title' as type FROM documents 
            WHERE title LIKE ? 
            UNION
            SELECT DISTINCT category as suggestion, 'category' as type FROM documents 
            WHERE category LIKE ?
            ORDER BY suggestion
            LIMIT ?
            """
            
            search_pattern = f"%{safe_query}%"
            cursor.execute(suggestions_sql, [search_pattern, search_pattern, limit])
            suggestions = cursor.fetchall()
            
            conn.close()
            
            return [{'text': row[0], 'type': row[1]} for row in suggestions]
            
        except Exception as e:
            print(f"获取搜索建议错误: {e}")
            return []
    
    def get_popular_searches(self, limit=10):
        """
        获取热门搜索词（这里简化为最新文档的标题关键词）
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT title, category FROM documents 
            ORDER BY created_at DESC 
            LIMIT ?
            """, [limit])
            
            results = cursor.fetchall()
            conn.close()
            
            # 提取关键词（简化实现）
            keywords = set()
            for row in results:
                # 从标题中提取关键词
                title_words = re.findall(r'\b\w{3,}\b', row[0])
                keywords.update(word.lower() for word in title_words)
                
                # 添加分类
                if row[1]:
                    keywords.add(row[1].lower())
            
            return list(keywords)[:limit]
            
        except Exception as e:
            print(f"获取热门搜索错误: {e}")
            return []

# 初始化搜索引擎
def get_search_engine():
    """获取搜索引擎实例"""
    db_path = os.environ.get('SQLITE_DATABASE_URL', 'sqlite:///ros2_wiki.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]  # 移除 'sqlite:///' 前缀
    return SearchEngine(db_path)

# 路由定义
@search_bp.route('/')
def search_page():
    """搜索页面"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    if query:
        search_engine = get_search_engine()
        offset = (page - 1) * per_page
        results = search_engine.full_text_search(query, limit=per_page, offset=offset)
    else:
        results = {'results': [], 'total': 0, 'query': ''}
    
    return render_template('search/results.html', **results)

@search_bp.route('/api')
def search_api():
    """搜索API接口"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 50)  # 限制每页最大数量
    
    if not query:
        return jsonify({'error': '搜索查询不能为空'}), 400
    
    search_engine = get_search_engine()
    offset = (page - 1) * per_page
    results = search_engine.full_text_search(query, limit=per_page, offset=offset)
    
    return jsonify(results)

@search_bp.route('/suggestions')
def search_suggestions():
    """搜索建议API"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 5)), 20)
    
    search_engine = get_search_engine()
    suggestions = search_engine.get_search_suggestions(query, limit)
    
    return jsonify({'suggestions': suggestions})

@search_bp.route('/popular')
def popular_searches():
    """热门搜索API"""
    limit = min(int(request.args.get('limit', 10)), 50)
    
    search_engine = get_search_engine()
    popular = search_engine.get_popular_searches(limit)
    
    return jsonify({'popular_searches': popular})