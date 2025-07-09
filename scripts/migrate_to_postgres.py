#!/usr/bin/env python3
"""
数据库迁移工具 - 从SQLite迁移到PostgreSQL
使用方法: python migrate_to_postgres.py
"""
import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import click
from werkzeug.security import generate_password_hash


class DatabaseMigrator:
    """数据库迁移器"""
    
    def __init__(self, sqlite_path: str, postgres_url: str):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.sqlite_conn = None
        self.pg_conn = None
    
    def connect(self):
        """连接数据库"""
        # 连接SQLite
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        # 连接PostgreSQL
        self.pg_conn = psycopg2.connect(self.postgres_url)
        self.pg_conn.autocommit = False
    
    def close(self):
        """关闭连接"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()
    
    def create_postgres_schema(self):
        """创建PostgreSQL表结构"""
        click.echo("创建PostgreSQL表结构...")
        
        with self.pg_conn.cursor() as cur:
            # 创建用户表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(128),
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """)
            
            # 创建文档表 - 增强版
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    view_count INTEGER DEFAULT 0,
                    metadata JSONB DEFAULT '{}',
                    search_vector tsvector
                );
                
                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
                CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
                CREATE INDEX IF NOT EXISTS idx_documents_search ON documents USING GIN(search_vector);
                
                -- 创建触发器自动更新search_vector
                CREATE OR REPLACE FUNCTION documents_search_trigger() RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector := 
                        setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('simple', COALESCE(NEW.content, '')), 'B');
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS documents_search_update ON documents;
                CREATE TRIGGER documents_search_update 
                BEFORE INSERT OR UPDATE ON documents
                FOR EACH ROW EXECUTE FUNCTION documents_search_trigger();
            """)
            
            # 创建评论表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_comments_document_id ON comments(document_id);
                CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);
                CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at DESC);
            """)
            
            self.pg_conn.commit()
            click.echo("✓ 表结构创建完成")
    
    def migrate_users(self):
        """迁移用户数据"""
        click.echo("迁移用户数据...")
        
        # 从SQLite读取
        sqlite_cur = self.sqlite_conn.cursor()
        users = sqlite_cur.execute("SELECT * FROM users").fetchall()
        
        with self.pg_conn.cursor() as pg_cur:
            for user in users:
                pg_cur.execute("""
                    INSERT INTO users (id, username, email, password_hash, is_admin, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    user['id'],
                    user['username'],
                    user['email'],
                    user['password_hash'],
                    bool(user['is_admin']),
                    user['created_at'] or datetime.now()
                ))
            
            # 重置序列
            pg_cur.execute("""
                SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))
            """)
            
            self.pg_conn.commit()
            click.echo(f"✓ 迁移了 {len(users)} 个用户")
    
    def migrate_documents(self):
        """迁移文档数据"""
        click.echo("迁移文档数据...")
        
        sqlite_cur = self.sqlite_conn.cursor()
        documents = sqlite_cur.execute("SELECT * FROM documents").fetchall()
        
        with self.pg_conn.cursor() as pg_cur:
            for doc in documents:
                # 准备metadata字段（未来扩展用）
                metadata = {
                    'migrated_from': 'sqlite',
                    'migration_date': datetime.now().isoformat()
                }
                
                pg_cur.execute("""
                    INSERT INTO documents 
                    (id, title, content, category, user_id, created_at, updated_at, view_count, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    doc['id'],
                    doc['title'],
                    doc['content'],
                    doc['category'],
                    doc['user_id'],
                    doc['created_at'] or datetime.now(),
                    doc['updated_at'] or datetime.now(),
                    doc['view_count'] or 0,
                    psycopg2.extras.Json(metadata)
                ))
            
            # 重置序列
            pg_cur.execute("""
                SELECT setval('documents_id_seq', (SELECT MAX(id) FROM documents))
            """)
            
            self.pg_conn.commit()
            click.echo(f"✓ 迁移了 {len(documents)} 篇文档")
    
    def migrate_comments(self):
        """迁移评论数据"""
        click.echo("迁移评论数据...")
        
        sqlite_cur = self.sqlite_conn.cursor()
        comments = sqlite_cur.execute("SELECT * FROM comments").fetchall()
        
        with self.pg_conn.cursor() as pg_cur:
            for comment in comments:
                pg_cur.execute("""
                    INSERT INTO comments 
                    (id, content, user_id, document_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    comment['id'],
                    comment['content'],
                    comment['user_id'],
                    comment['document_id'],
                    comment['created_at'] or datetime.now(),
                    comment['updated_at'] or datetime.now()
                ))
            
            # 重置序列
            pg_cur.execute("""
                SELECT setval('comments_id_seq', (SELECT MAX(id) FROM comments))
            """)
            
            self.pg_conn.commit()
            click.echo(f"✓ 迁移了 {len(comments)} 条评论")
    
    def verify_migration(self):
        """验证迁移结果"""
        click.echo("\n验证迁移结果...")
        
        with self.pg_conn.cursor(cursor_factory=RealDictCursor) as pg_cur:
            # 检查记录数
            for table in ['users', 'documents', 'comments']:
                pg_cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = pg_cur.fetchone()['count']
                click.echo(f"  {table}: {count} 条记录")
            
            # 测试全文搜索
            pg_cur.execute("""
                SELECT title FROM documents 
                WHERE search_vector @@ to_tsquery('simple', 'test')
                LIMIT 5
            """)
            results = pg_cur.fetchall()
            click.echo(f"\n全文搜索测试 - 搜索'test'找到 {len(results)} 个结果")
    
    def migrate(self):
        """执行完整迁移"""
        try:
            self.connect()
            self.create_postgres_schema()
            self.migrate_users()
            self.migrate_documents() 
            self.migrate_comments()
            self.verify_migration()
            click.echo("\n✅ 数据库迁移成功完成！")
        except Exception as e:
            click.echo(f"\n❌ 迁移失败: {str(e)}", err=True)
            if self.pg_conn:
                self.pg_conn.rollback()
            raise
        finally:
            self.close()


@click.command()
@click.option('--sqlite-path', default='ros2_wiki.db', help='SQLite数据库路径')
@click.option('--postgres-url', help='PostgreSQL连接URL')
@click.option('--dry-run', is_flag=True, help='仅测试连接，不执行迁移')
def main(sqlite_path, postgres_url, dry_run):
    """ROS2 Wiki 数据库迁移工具"""
    
    if not postgres_url:
        # 从环境变量或配置文件读取
        postgres_url = os.environ.get('POSTGRES_URL', 
            'postgresql://postgres:password@localhost:5432/ros2_wiki')
    
    click.echo(f"SQLite路径: {sqlite_path}")
    click.echo(f"PostgreSQL URL: {postgres_url}")
    
    if dry_run:
        click.echo("\n运行模式: 测试连接")
        migrator = DatabaseMigrator(sqlite_path, postgres_url)
        try:
            migrator.connect()
            click.echo("✓ 数据库连接成功")
            migrator.close()
        except Exception as e:
            click.echo(f"✗ 连接失败: {str(e)}", err=True)
    else:
        if click.confirm('\n确定要开始迁移吗？建议先备份数据'):
            migrator = DatabaseMigrator(sqlite_path, postgres_url)
            migrator.migrate()


if __name__ == '__main__':
    main()