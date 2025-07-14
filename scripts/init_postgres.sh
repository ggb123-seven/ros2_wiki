#!/bin/bash
# PostgreSQL数据库初始化脚本

echo "=== ROS2 Wiki PostgreSQL初始化脚本 ==="
echo ""

# 默认配置
DB_NAME="ros2_wiki"
DB_USER="postgres"
DB_PASS="postgres123"
DB_HOST="localhost"
DB_PORT="5432"

# 检查是否提供了自定义参数
if [ "$1" == "--help" ]; then
    echo "使用方法: ./init_postgres.sh [DB_NAME] [DB_USER] [DB_PASS] [DB_HOST] [DB_PORT]"
    echo "默认值: ros2_wiki postgres postgres123 localhost 5432"
    exit 0
fi

# 使用提供的参数或默认值
[ -n "$1" ] && DB_NAME=$1
[ -n "$2" ] && DB_USER=$2
[ -n "$3" ] && DB_PASS=$3
[ -n "$4" ] && DB_HOST=$4
[ -n "$5" ] && DB_PORT=$5

echo "数据库配置:"
echo "  数据库名: $DB_NAME"
echo "  用户名: $DB_USER"
echo "  主机: $DB_HOST"
echo "  端口: $DB_PORT"
echo ""

# 生成数据库连接URL
DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"
echo "数据库连接URL: $DATABASE_URL"
echo ""

# 检查PostgreSQL是否运行
echo "检查PostgreSQL服务状态..."
if command -v pg_isready &> /dev/null; then
    pg_isready -h $DB_HOST -p $DB_PORT
    if [ $? -ne 0 ]; then
        echo "❌ PostgreSQL服务未运行"
        echo "请先启动PostgreSQL服务："
        echo "  Ubuntu/Debian: sudo service postgresql start"
        echo "  或使用Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=$DB_PASS postgres:15"
        exit 1
    fi
else
    echo "⚠️  无法检查PostgreSQL状态（pg_isready不可用）"
fi

# 创建数据库（如果不存在）
echo ""
echo "创建数据库..."
if command -v createdb &> /dev/null; then
    createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ 数据库 '$DB_NAME' 创建成功"
    else
        echo "ℹ️  数据库可能已存在或需要密码"
    fi
else
    echo "⚠️  createdb命令不可用，跳过数据库创建"
fi

# 创建初始化SQL文件
echo ""
echo "创建数据库初始化SQL..."
cat > /tmp/ros2_wiki_init.sql << 'EOF'
-- ROS2 Wiki PostgreSQL初始化脚本

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 创建文档表
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

-- 创建文档索引
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_search ON documents USING GIN(search_vector);

-- 创建全文搜索触发器
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

-- 创建评论表
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建评论索引
CREATE INDEX IF NOT EXISTS idx_comments_document_id ON comments(document_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at DESC);

-- 创建统计视图
CREATE OR REPLACE VIEW document_stats AS
SELECT 
    d.category,
    COUNT(*) as document_count,
    AVG(d.view_count) as avg_views,
    MAX(d.created_at) as latest_document,
    COUNT(DISTINCT c.id) as total_comments
FROM documents d
LEFT JOIN comments c ON d.id = c.document_id
GROUP BY d.category;

-- 插入默认管理员（仅用于开发）
INSERT INTO users (username, email, password_hash, is_admin)
VALUES ('admin', 'admin@ros2wiki.local', 'scrypt:32768:8:1$xLr5H6KwqsMgJeL8$3f4e6566088da90ebce0c77288a8eed4cd554c589354e1b479e914a0ce825e0e2b87de6b5e923f9f077a390103f20e3708f9dd6dd2a12f2e4bb0ecdc98de48d6', true)
ON CONFLICT (username) DO NOTHING;

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '✅ ROS2 Wiki PostgreSQL数据库初始化完成！';
    RAISE NOTICE '默认管理员账号: admin / admin123';
    RAISE NOTICE '⚠️  请在生产环境中修改默认密码！';
END $$;
EOF

echo "✅ SQL文件创建成功: /tmp/ros2_wiki_init.sql"

# 更新.env文件中的数据库URL
echo ""
echo "更新.env文件..."
if [ -f ".env" ]; then
    # 备份原始文件
    cp .env .env.backup
    # 更新DATABASE_URL
    sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env
    echo "✅ .env文件已更新"
else
    echo "⚠️  .env文件不存在"
fi

echo ""
echo "=== 初始化完成 ==="
echo ""
echo "下一步："
echo "1. 如果PostgreSQL正在运行，执行SQL初始化："
echo "   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /tmp/ros2_wiki_init.sql"
echo ""
echo "2. 或者使用Python脚本进行数据迁移："
echo "   python3 scripts/migrate_to_postgres.py"
echo ""
echo "3. 启动应用："
echo "   export DATABASE_URL=\"$DATABASE_URL\""
echo "   python3 app.py"