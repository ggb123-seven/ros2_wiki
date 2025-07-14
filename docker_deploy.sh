#!/bin/bash
# Docker Compose 一键启动脚本

set -e

echo "🚀 ROS2 Wiki Docker部署"

# 创建Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app_postgres.py"]
EOF

# 检查docker和docker-compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    echo "安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose未安装，尝试使用docker compose"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# 生成随机密码
POSTGRES_PASSWORD=$(openssl rand -base64 12)
SECRET_KEY=$(openssl rand -hex 32)

# 更新docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ros2_wiki
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/ros2_wiki
      SECRET_KEY: ${SECRET_KEY}
      FLASK_ENV: production
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
EOF

# 创建.env文件
cat > .env.docker << EOF
# Docker环境配置
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/ros2_wiki
EOF

echo "✅ Docker配置文件已生成"
echo ""
echo "📋 配置信息已保存到 .env.docker"
echo ""
echo "🔧 启动服务..."

# 构建并启动
$COMPOSE_CMD up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 初始化数据库
echo "🗄️  初始化数据库..."
$COMPOSE_CMD exec -T web python scripts/init_postgres_db.py

echo ""
echo "✅ 部署完成！"
echo ""
echo "🌐 访问地址: http://localhost:5000"
echo "👤 管理员账号: admin / admin123"
echo ""
echo "📝 常用命令:"
echo "  查看日志: $COMPOSE_CMD logs -f"
echo "  停止服务: $COMPOSE_CMD down"
echo "  重启服务: $COMPOSE_CMD restart"
echo "  查看状态: $COMPOSE_CMD ps"