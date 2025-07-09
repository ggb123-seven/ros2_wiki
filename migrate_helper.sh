#!/bin/bash
# ROS2 Wiki PostgreSQL迁移助手

set -e  # 遇到错误立即退出

echo "======================================"
echo "ROS2 Wiki PostgreSQL 迁移助手"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 检查Python3
echo "1. 检查系统环境..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3未安装"
    exit 1
fi
print_success "Python3已安装: $(python3 --version)"

# 检查PostgreSQL客户端
if command -v psql &> /dev/null; then
    print_success "PostgreSQL客户端已安装"
else
    print_warning "PostgreSQL客户端未安装，某些功能可能受限"
fi

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_success "已加载.env配置文件"
else
    print_error ".env文件不存在"
    echo "请先复制.env.example并配置数据库连接信息"
    exit 1
fi

# 显示数据库配置
echo ""
echo "2. 数据库配置:"
echo "   DATABASE_URL: $DATABASE_URL"
echo ""

# 选择操作
echo "请选择操作:"
echo "1) 初始化新的PostgreSQL数据库"
echo "2) 从SQLite迁移数据到PostgreSQL"
echo "3) 测试PostgreSQL连接"
echo "4) 启动应用（PostgreSQL版本）"
echo "5) 运行测试"
echo "0) 退出"
echo ""
read -p "请输入选项 (0-5): " choice

case $choice in
    1)
        echo ""
        echo "初始化PostgreSQL数据库..."
        python3 scripts/init_postgres_db.py
        ;;
    
    2)
        echo ""
        echo "从SQLite迁移到PostgreSQL..."
        if [ -f "ros2_wiki.db" ]; then
            print_success "找到SQLite数据库文件"
            python3 scripts/migrate_to_postgres.py
        else
            print_warning "未找到SQLite数据库文件"
            echo "将创建新的PostgreSQL数据库..."
            python3 scripts/init_postgres_db.py
        fi
        ;;
    
    3)
        echo ""
        echo "测试PostgreSQL连接..."
        python3 -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.environ.get('DATABASE_URL'))
    conn = engine.connect()
    result = conn.execute('SELECT version()')
    version = result.fetchone()[0]
    print(f'✅ 连接成功！')
    print(f'PostgreSQL版本: {version}')
    conn.close()
except Exception as e:
    print(f'❌ 连接失败: {str(e)}')
"
        ;;
    
    4)
        echo ""
        echo "启动应用（PostgreSQL版本）..."
        print_warning "按Ctrl+C停止应用"
        python3 app_postgres.py
        ;;
    
    5)
        echo ""
        echo "运行测试..."
        if command -v pytest &> /dev/null; then
            pytest tests/ -v
        else
            print_warning "pytest未安装，尝试使用python -m pytest"
            python3 -m pytest tests/ -v || print_error "测试运行失败，请安装pytest"
        fi
        ;;
    
    0)
        echo "退出"
        exit 0
        ;;
    
    *)
        print_error "无效的选项"
        exit 1
        ;;
esac

echo ""
echo "======================================"
print_success "操作完成！"
echo ""
echo "下一步建议:"
echo "- 如果刚初始化数据库，运行选项4启动应用"
echo "- 访问 http://localhost:5000"
echo "- 使用 admin/admin123 登录"
echo "- 记得在生产环境中修改默认密码！"
echo "======================================"