-- 优化的查询模板 - 米醋电子工作室
-- 生成时间: 2025-07-17 15:03:55.994101

-- full_text_search

                SELECT d.id, d.title, d.content, d.category, d.created_at, u.username as author
                FROM documents_fts fts
                JOIN documents d ON fts.rowid = d.id
                LEFT JOIN users u ON d.author_id = u.id
                WHERE documents_fts MATCH ?
                ORDER BY bm25(documents_fts) LIMIT ?;
            

-- category_search

                SELECT id, title, content, category, created_at
                FROM documents 
                WHERE category = ?
                ORDER BY created_at DESC 
                LIMIT ?;
            

-- author_documents

                SELECT d.id, d.title, d.category, d.created_at
                FROM documents d
                WHERE d.author_id = ?
                ORDER BY d.created_at DESC
                LIMIT ?;
            

-- recent_documents

                SELECT d.id, d.title, d.category, d.created_at, u.username as author
                FROM documents d
                LEFT JOIN users u ON d.author_id = u.id
                ORDER BY d.created_at DESC
                LIMIT ?;
            

-- popular_categories

                SELECT category, COUNT(*) as doc_count
                FROM documents
                GROUP BY category
                ORDER BY doc_count DESC;
            

