#!/usr/bin/env python3
"""
数据库性能优化工具 - 添加关键索引
米醋电子工作室 - SuperClaude性能优化
"""

import sqlite3
import os
from datetime import datetime

class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, db_path=None):
        # 云端环境适配：优先使用PostgreSQL，fallback到SQLite
        if db_path is None:
            # 检查是否为云端环境
            if os.environ.get('DATABASE_URL'):
                self.db_path = 'postgresql'  # 标记为PostgreSQL
                self.database_url = os.environ.get('DATABASE_URL')
            else:
                self.db_path = 'ros2_wiki.db'  # 本地SQLite
        else:
            self.db_path = db_path
        
    def create_performance_indexes(self):
        """创建性能优化索引"""
        
        optimization_sql = """
        -- 用户表索引
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
        
        -- 文档表索引
        CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
        CREATE INDEX IF NOT EXISTS idx_documents_author_id ON documents(author_id);
        CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
        CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
        CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at);
        
        -- 复合索引用于常见查询模式
        CREATE INDEX IF NOT EXISTS idx_documents_category_created ON documents(category, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_documents_author_created ON documents(author_id, created_at DESC);
        
        -- 全文搜索索引 (SQLite FTS)
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            title, 
            content, 
            category,
            content='documents',
            content_rowid='id'
        );
        
        -- FTS索引触发器
        CREATE TRIGGER IF NOT EXISTS documents_fts_insert AFTER INSERT ON documents BEGIN
            INSERT INTO documents_fts(rowid, title, content, category) 
            VALUES (new.id, new.title, new.content, new.category);
        END;
        
        CREATE TRIGGER IF NOT EXISTS documents_fts_delete AFTER DELETE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, title, content, category) 
            VALUES('delete', old.id, old.title, old.content, old.category);
        END;
        
        CREATE TRIGGER IF NOT EXISTS documents_fts_update AFTER UPDATE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, title, content, category) 
            VALUES('delete', old.id, old.title, old.content, old.category);
            INSERT INTO documents_fts(rowid, title, content, category) 
            VALUES (new.id, new.title, new.content, new.category);
        END;
        
        -- 评论表索引（如果存在）
        CREATE INDEX IF NOT EXISTS idx_comments_document_id ON comments(document_id);
        CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);
        CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at);
        
        -- 用户日志表索引（如果存在）
        CREATE INDEX IF NOT EXISTS idx_user_logs_user_id ON user_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_logs_action ON user_logs(action);
        CREATE INDEX IF NOT EXISTS idx_user_logs_timestamp ON user_logs(timestamp);
        """
        
        try:
            # 检查数据库类型
            if self.db_path == 'postgresql':
                # PostgreSQL环境，跳过索引创建（通过app自动处理）
                print("检测到PostgreSQL环境，索引将在应用启动时创建")
                return True
            
            # SQLite环境
            if not os.path.exists(self.db_path):
                print(f"数据库文件不存在: {os.path.abspath(self.db_path)}")
                print("跳过索引创建，数据库将在应用启动时初始化")
                return True
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print("开始创建数据库索引...")
            
            # 执行索引创建
            for statement in optimization_sql.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                        print(f"执行: {statement[:50]}...")
                    except sqlite3.Error as e:
                        print(f"警告: {e}")
            
            conn.commit()
            print("索引创建完成！")
            
            # 分析表统计信息
            cursor.execute("ANALYZE;")
            conn.commit()
            
            print("数据库统计信息更新完成！")
            
        except sqlite3.Error as e:
            print(f"数据库优化失败: {e}")
        finally:
            if conn:
                conn.close()
    
    def create_optimized_search_queries(self):
        """创建优化的搜索查询模板"""
        
        search_queries = {
            'full_text_search': """
                SELECT d.id, d.title, d.content, d.category, d.created_at, u.username as author
                FROM documents_fts fts
                JOIN documents d ON fts.rowid = d.id
                LEFT JOIN users u ON d.author_id = u.id
                WHERE documents_fts MATCH ?
                ORDER BY bm25(documents_fts) LIMIT ?;
            """,
            
            'category_search': """
                SELECT id, title, content, category, created_at
                FROM documents 
                WHERE category = ?
                ORDER BY created_at DESC 
                LIMIT ?;
            """,
            
            'author_documents': """
                SELECT d.id, d.title, d.category, d.created_at
                FROM documents d
                WHERE d.author_id = ?
                ORDER BY d.created_at DESC
                LIMIT ?;
            """,
            
            'recent_documents': """
                SELECT d.id, d.title, d.category, d.created_at, u.username as author
                FROM documents d
                LEFT JOIN users u ON d.author_id = u.id
                ORDER BY d.created_at DESC
                LIMIT ?;
            """,
            
            'popular_categories': """
                SELECT category, COUNT(*) as doc_count
                FROM documents
                GROUP BY category
                ORDER BY doc_count DESC;
            """
        }
        
        # 保存查询模板到文件
        with open('optimized_queries.sql', 'w', encoding='utf-8') as f:
            f.write("-- 优化的查询模板 - 米醋电子工作室\n")
            f.write(f"-- 生成时间: {datetime.now()}\n\n")
            
            for name, query in search_queries.items():
                f.write(f"-- {name}\n")
                f.write(query)
                f.write("\n\n")
        
        print("优化查询模板已保存到 optimized_queries.sql")
        
        return search_queries
    
    def check_index_usage(self):
        """检查索引使用情况"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查已创建的索引
            cursor.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
                ORDER BY name;
            """)
            
            indexes = cursor.fetchall()
            print(f"已创建索引数量: {len(indexes)}")
            
            for name, sql in indexes:
                print(f"  - {name}")
            
            # 检查表大小
            cursor.execute("SELECT COUNT(*) FROM documents;")
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            
            print(f"文档数量: {doc_count}")
            print(f"用户数量: {user_count}")
            
        except sqlite3.Error as e:
            print(f"检查索引失败: {e}")
        finally:
            if conn:
                conn.close()

def main():
    """主执行函数"""
    print("SuperClaude数据库优化工具启动...")
    
    db_path = 'F:/ros2_wiki/ros2_wiki.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    optimizer = DatabaseOptimizer(db_path)
    
    # 创建索引
    optimizer.create_performance_indexes()
    
    # 创建优化查询
    optimizer.create_optimized_search_queries()
    
    # 检查索引状态
    optimizer.check_index_usage()
    
    print("数据库优化完成！")

if __name__ == "__main__":
    main()