# 统一部署脚本

#!/bin/bash

# ROS2 Wiki 统一部署脚本
# 支持开发、测试、生产环境的一键部署

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
ROS2 Wiki 统一部署脚本

用法: ./deploy.sh [选项] [环境]

环境:
  dev         开发环境 (默认)
  test        测试环境  
  prod        生产环境

选项:
  -h, --help     显示帮助信息
  -v, --verbose  详细输出
  -f, --force    强制重新构建
  -d, --down     停止并删除容器
  -l, --logs     查看日志
  -s, --status   查看服务状态
  -b, --backup   创建数据备份
  -r, --restore  恢复数据备份

示例:
  ./deploy.sh dev              # 部署开发环境
  ./deploy.sh prod --force     # 强制重新部署生产环境
  ./deploy.sh --status         # 查看当前状态
  ./deploy.sh --logs           # 查看日志
  ./deploy.sh --backup         # 创建备份

EOF
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 检查环境变量文件
check_env_file() {
    local env=$1
    local env_file=".env.${env}"
    
    if [[ ! -f "$env_file" ]]; then
        log_warning "环境文件 $env_file 不存在，使用默认 .env 文件"
        env_file=".env"
    fi
    
    if [[ ! -f "$env_file" ]]; then
        log_error "环境文件不存在，请创建 $env_file 或 .env 文件"
        exit 1
    fi
    
    export ENV_FILE="$env_file"
    log_info "使用环境文件: $env_file"
}

# 生成安全密钥
generate_secrets() {
    log_info "检查安全配置..."
    
    if [[ ! -f ".env" ]]; then
        log_info "创建默认环境配置..."
        cp .env.example .env
    fi
    
    # 检查是否需要生成新的SECRET_KEY
    if grep -q "your-super-secret-key-change-this" .env; then
        log_info "生成新的安全密钥..."
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i "s/your-super-secret-key-change-this/$SECRET_KEY/g" .env
        log_success "安全密钥已更新"
    fi
}

# 构建镜像
build_images() {
    local force=$1
    log_info "构建Docker镜像..."
    
    if [[ "$force" == "true" ]]; then
        docker-compose -f docker-compose.unified.yml build --no-cache
    else
        docker-compose -f docker-compose.unified.yml build
    fi
    
    log_success "镜像构建完成"
}

# 部署服务
deploy_services() {
    local env=$1
    local profiles=""
    
    case $env in
        "prod")
            profiles="--profile production"
            log_info "部署生产环境..."
            ;;
        "test")
            log_info "部署测试环境..."
            ;;
        "dev"|*)
            log_info "部署开发环境..."
            ;;
    esac
    
    # 创建必要的目录
    mkdir -p logs uploads data backups nginx/sites-available ssl
    
    # 启动服务
    docker-compose -f docker-compose.unified.yml --env-file $ENV_FILE up -d $profiles
    
    log_success "服务部署完成"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose -f docker-compose.unified.yml down
    log_success "服务已停止"
}

# 查看状态
show_status() {
    log_info "服务状态:"
    docker-compose -f docker-compose.unified.yml ps
    
    echo ""
    log_info "健康检查:"
    docker-compose -f docker-compose.unified.yml exec ros2-wiki curl -f http://localhost:5000/api/health || true
}

# 查看日志
show_logs() {
    local service=${1:-""}
    if [[ -n "$service" ]]; then
        docker-compose -f docker-compose.unified.yml logs -f "$service"
    else
        docker-compose -f docker-compose.unified.yml logs -f
    fi
}

# 创建备份
create_backup() {
    log_info "创建数据备份..."
    
    backup_dir="./backups/manual"
    mkdir -p "$backup_dir"
    
    timestamp=$(date +%Y%m%d-%H%M%S)
    
    # 数据库备份
    docker-compose -f docker-compose.unified.yml exec db pg_dump -U postgres ros2_wiki > "$backup_dir/db-backup-$timestamp.sql"
    
    # 文件备份
    tar -czf "$backup_dir/files-backup-$timestamp.tar.gz" uploads/ static/uploads/ || true
    
    log_success "备份创建完成: $backup_dir/"
}

# 恢复备份
restore_backup() {
    local backup_file=$1
    
    if [[ -z "$backup_file" ]]; then
        log_error "请指定备份文件"
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log_warning "这将覆盖现有数据，确认继续吗？(y/N)"
    read -r confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "操作已取消"
        exit 0
    fi
    
    log_info "恢复数据备份..."
    docker-compose -f docker-compose.unified.yml exec -T db psql -U postgres -d ros2_wiki < "$backup_file"
    log_success "数据恢复完成"
}

# 安装SSL证书 (Let's Encrypt)
install_ssl() {
    local domain=$1
    
    if [[ -z "$domain" ]]; then
        log_error "请指定域名"
        exit 1
    fi
    
    log_info "为域名 $domain 安装SSL证书..."
    
    # 使用certbot获取证书
    docker run --rm -it \
        -v $(pwd)/ssl:/etc/letsencrypt \
        -p 80:80 \
        certbot/certbot certonly --standalone -d "$domain"
    
    log_success "SSL证书安装完成"
}

# 更新应用
update_app() {
    log_info "更新应用..."
    
    # 拉取最新代码
    git pull
    
    # 重新构建和部署
    build_images true
    docker-compose -f docker-compose.unified.yml up -d
    
    log_success "应用更新完成"
}

# 清理资源
cleanup() {
    log_info "清理未使用的资源..."
    
    docker system prune -f
    docker volume prune -f
    
    log_success "清理完成"
}

# 主函数
main() {
    local env="dev"
    local force=false
    local verbose=false
    local action="deploy"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                set -x
                shift
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -d|--down)
                action="down"
                shift
                ;;
            -l|--logs)
                action="logs"
                shift
                ;;
            -s|--status)
                action="status"
                shift
                ;;
            -b|--backup)
                action="backup"
                shift
                ;;
            -r|--restore)
                action="restore"
                shift
                ;;
            --ssl)
                action="ssl"
                shift
                ;;
            --update)
                action="update"
                shift
                ;;
            --cleanup)
                action="cleanup"
                shift
                ;;
            dev|test|prod)
                env=$1
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检查依赖
    check_dependencies
    
    # 执行操作
    case $action in
        "deploy")
            check_env_file "$env"
            generate_secrets
            build_images "$force"
            deploy_services "$env"
            show_status
            ;;
        "down")
            stop_services
            ;;
        "logs")
            show_logs "$env"
            ;;
        "status")
            show_status
            ;;
        "backup")
            create_backup
            ;;
        "restore")
            restore_backup "$2"
            ;;
        "ssl")
            install_ssl "$2"
            ;;
        "update")
            update_app
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            log_error "未知操作: $action"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"