#!/bin/bash
# ROS2 Wiki 全自动化部署脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_step() {
    echo -e "\n${BLUE}[$(date +%H:%M:%S)] ===> $1${NC}"
}

print_success() {
    echo -e "${GREEN}[✓] $1${NC}"
}

print_error() {
    echo -e "${RED}[✗] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# 检查命令是否存在
check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 已安装"
        return 0
    else
        print_warning "$1 未安装"
        return 1
    fi
}

# 清理函数
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "部署过程中出现错误"
        # 清理可能的残留进程
        pkill -f "app_postgres.py" 2>/dev/null || true
        pkill -f "postgres" 2>/dev/null || true
    fi
}

trap cleanup EXIT

# 主函数
main() {
    echo -e "${BLUE}======================================"
    echo -e "ROS2 Wiki 全自动化部署"
    echo -e "======================================${NC}"
    
    # 步骤1：环境检查
    print_step "步骤1：检查系统环境"
    
    if ! check_command python3; then
        print_error "Python3 是必需的，请先安装"
        exit 1
    fi
    
    DOCKER_AVAILABLE=false
    if check_command docker; then
        DOCKER_AVAILABLE=true
    fi
    
    # 步骤2：准备Python环境
    print_step "步骤2：准备Python虚拟环境"
    
    if [ ! -d "venv" ]; then
        print_warning "创建Python虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建成功"
    else
        print_success "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 步骤3：安装依赖
    print_step "步骤3：安装Python依赖"
    
    # 升级pip
    python -m pip install --upgrade pip > /dev/null 2>&1
    
    # 安装依赖
    if python -m pip install -r requirements.txt > /tmp/pip_install.log 2>&1; then
        print_success "依赖安装成功"
    else
        print_error "依赖安装失败，查看日志: /tmp/pip_install.log"
        exit 1
    fi
    
    # 步骤4：启动PostgreSQL
    print_step "步骤4：启动PostgreSQL数据库"
    
    # 检查是否已有PostgreSQL运行
    PG_RUNNING=false
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        print_success "PostgreSQL已在运行"
        PG_RUNNING=true
    elif [ "$DOCKER_AVAILABLE" = true ]; then
        # 使用Docker启动PostgreSQL
        print_warning "使用Docker启动PostgreSQL..."
        
        # 检查是否已有容器
        if docker ps -a | grep -q ros2_wiki_postgres; then
            docker start ros2_wiki_postgres > /dev/null 2>&1
            print_success "PostgreSQL容器已启动"
        else
            # 创建新容器
            docker run -d \
                --name ros2_wiki_postgres \
                -e POSTGRES_USER=postgres \
                -e POSTGRES_PASSWORD=postgres123 \
                -e POSTGRES_DB=ros2_wiki \
                -p 5432:5432 \
                postgres:15-alpine > /dev/null 2>&1
            
            print_success "PostgreSQL容器创建成功"
            print_warning "等待数据库启动..."
            sleep 5
        fi
        PG_RUNNING=true
    else
        print_warning "请手动启动PostgreSQL或安装Docker"
        print_warning "尝试使用SQLite模式..."
    fi
    
    # 步骤5：初始化数据库
    print_step "步骤5：初始化数据库结构"
    
    if [ "$PG_RUNNING" = true ]; then
        # 使用PostgreSQL
        export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/ros2_wiki"
        
        # 等待PostgreSQL完全启动
        for i in {1..10}; do
            if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        # 初始化数据库
        if python scripts/init_postgres_db.py > /tmp/db_init.log 2>&1; then
            print_success "PostgreSQL数据库初始化成功"
        else
            print_error "数据库初始化失败，查看日志: /tmp/db_init.log"
            cat /tmp/db_init.log
            exit 1
        fi
    else
        # 回退到SQLite
        export DATABASE_URL="sqlite:///ros2_wiki.db"
        print_warning "使用SQLite数据库"
    fi
    
    # 步骤6：生成SECRET_KEY
    print_step "步骤6：生成安全密钥"
    
    if [ ! -f ".env.production" ]; then
        SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
        cat > .env.production << EOF
# 生产环境配置
SECRET_KEY=$SECRET_KEY
DATABASE_URL=$DATABASE_URL
FLASK_ENV=production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
EOF
        print_success "生产环境配置已生成"
    fi
    
    # 步骤7：创建启动脚本
    print_step "步骤7：创建启动脚本"
    
    cat > start_app.sh << 'EOF'
#!/bin/bash
# 应用启动脚本

# 激活虚拟环境
source venv/bin/activate

# 加载环境变量
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# 启动应用
echo "启动ROS2 Wiki应用..."
echo "访问地址: http://localhost:5000"
echo "管理员账号: admin / admin123"
echo "按 Ctrl+C 停止应用"
echo ""

# 使用生产模式启动
exec python app_postgres.py
EOF
    chmod +x start_app.sh
    print_success "启动脚本创建成功"
    
    # 步骤8：创建系统服务（可选）
    print_step "步骤8：创建管理脚本"
    
    cat > manage.sh << 'EOF'
#!/bin/bash
# ROS2 Wiki 管理脚本

case "$1" in
    start)
        echo "启动ROS2 Wiki..."
        nohup ./start_app.sh > app.log 2>&1 &
        echo $! > app.pid
        echo "应用已在后台启动，PID: $(cat app.pid)"
        echo "查看日志: tail -f app.log"
        ;;
    stop)
        if [ -f app.pid ]; then
            PID=$(cat app.pid)
            kill $PID 2>/dev/null
            rm -f app.pid
            echo "应用已停止"
        else
            echo "应用未运行"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f app.pid ] && kill -0 $(cat app.pid) 2>/dev/null; then
            echo "应用正在运行，PID: $(cat app.pid)"
        else
            echo "应用未运行"
        fi
        ;;
    logs)
        if [ -f app.log ]; then
            tail -f app.log
        else
            echo "日志文件不存在"
        fi
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF
    chmod +x manage.sh
    print_success "管理脚本创建成功"
    
    # 完成
    echo -e "\n${GREEN}======================================"
    echo -e "🎉 部署完成！"
    echo -e "======================================${NC}"
    
    echo -e "\n${YELLOW}重要信息：${NC}"
    echo "1. 数据库: $DATABASE_URL"
    echo "2. 默认管理员: admin / admin123"
    echo "3. 请立即修改默认密码！"
    
    echo -e "\n${YELLOW}启动应用：${NC}"
    echo "方式1 (前台运行): ./start_app.sh"
    echo "方式2 (后台运行): ./manage.sh start"
    
    echo -e "\n${YELLOW}管理命令：${NC}"
    echo "./manage.sh start   - 启动应用"
    echo "./manage.sh stop    - 停止应用"
    echo "./manage.sh restart - 重启应用"
    echo "./manage.sh status  - 查看状态"
    echo "./manage.sh logs    - 查看日志"
    
    # 询问是否立即启动
    echo -e "\n${YELLOW}是否立即启动应用？(y/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./start_app.sh
    fi
}

# 执行主函数
main