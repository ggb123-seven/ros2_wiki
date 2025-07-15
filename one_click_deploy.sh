#!/bin/bash

# 🚀 ROS2 Wiki 一键部署脚本
# 自动化部署到多个云平台

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查必需的工具
check_requirements() {
    print_header "检查部署环境"
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        print_error "Git 未安装，请先安装 Git"
        exit 1
    fi
    print_message "✅ Git 已安装"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，请先安装 Python3"
        exit 1
    fi
    print_message "✅ Python3 已安装"
    
    # 检查curl
    if ! command -v curl &> /dev/null; then
        print_warning "curl 未安装，部分测试功能可能不可用"
    else
        print_message "✅ curl 已安装"
    fi
}

# 验证项目配置
verify_project() {
    print_header "验证项目配置"
    
    # 检查必需文件
    required_files=("app.py" "requirements.txt" "render.yaml" "Procfile" "cloud_init_db.py")
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_message "✅ $file 存在"
        else
            print_error "❌ $file 不存在"
            exit 1
        fi
    done
    
    # 检查环境变量配置
    if grep -q "ADMIN_USERNAME.*ssss" render.yaml; then
        print_message "✅ 管理员配置正确"
    else
        print_error "❌ 管理员配置错误"
        exit 1
    fi
}

# 运行本地测试
run_tests() {
    print_header "运行本地测试"
    
    # 安装依赖
    print_message "安装Python依赖..."
    pip3 install -r requirements.txt > /dev/null 2>&1
    
    # 测试数据库初始化
    print_message "测试数据库初始化..."
    export AUTO_CREATE_ADMIN=true
    export ADMIN_USERNAME=ssss
    export ADMIN_EMAIL=seventee_0611@qq.com
    export ADMIN_PASSWORD=ssss123
    
    python3 -c "
from cloud_init_db import init_cloud_database
import sys
success = init_cloud_database()
print('✅ 数据库初始化测试通过!' if success else '❌ 数据库测试失败!')
sys.exit(0 if success else 1)
" || exit 1
    
    # 测试管理员账户
    print_message "测试管理员账户创建..."
    python3 -c "
import sqlite3
from werkzeug.security import check_password_hash
conn = sqlite3.connect('ros2_wiki.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash, is_admin FROM users WHERE username = ?', ('ssss',))
user = cursor.fetchone()
if user and user[2] and check_password_hash(user[1], 'ssss123'):
    print('✅ 管理员账户测试通过!')
    exit(0)
else:
    print('❌ 管理员账户测试失败!')
    exit(1)
" || exit 1
    
    print_message "✅ 所有本地测试通过!"
}

# 推送到GitHub
push_to_github() {
    print_header "推送代码到GitHub"
    
    # 检查Git状态
    if [ -n "$(git status --porcelain)" ]; then
        print_message "发现未提交的更改，正在提交..."
        git add .
        git commit -m "🚀 Auto deployment: $(date '+%Y-%m-%d %H:%M:%S')"
    else
        print_message "代码已是最新状态"
    fi
    
    # 推送到远程仓库
    print_message "推送到GitHub..."
    git push origin main || {
        print_error "推送失败，请检查网络连接和权限"
        exit 1
    }
    
    print_message "✅ 代码已推送到GitHub"
}

# 部署到Render.com
deploy_to_render() {
    print_header "部署到 Render.com"
    
    print_message "📋 Render.com 部署说明:"
    echo "1. 访问 https://render.com"
    echo "2. 连接GitHub仓库: ggb123-seven/ros2_wiki"
    echo "3. 选择 Web Service"
    echo "4. Render会自动读取 render.yaml 配置"
    echo "5. 等待部署完成"
    echo ""
    echo "🔑 管理员登录信息:"
    echo "   用户名: ssss"
    echo "   密码: ssss123"
    echo "   邮箱: seventee_0611@qq.com"
    echo ""
    
    read -p "是否已在Render.com上配置部署? (y/n): " render_configured
    if [ "$render_configured" = "y" ]; then
        print_message "✅ Render.com 部署已配置"
        
        # 如果有Render URL，测试部署
        if [ -n "$RENDER_URL" ]; then
            print_message "测试Render部署..."
            sleep 30  # 等待部署完成
            
            if curl -f "$RENDER_URL" > /dev/null 2>&1; then
                print_message "✅ Render部署测试成功!"
                echo "🌐 访问地址: $RENDER_URL"
            else
                print_warning "⚠️ Render部署测试失败，请手动检查"
            fi
        fi
    else
        print_warning "请手动在Render.com上配置部署"
    fi
}

# 部署到Railway.app
deploy_to_railway() {
    print_header "部署到 Railway.app"
    
    print_message "📋 Railway.app 部署说明:"
    echo "1. 访问 https://railway.app"
    echo "2. 选择 'Deploy from GitHub repo'"
    echo "3. 选择仓库: ggb123-seven/ros2_wiki"
    echo "4. 添加PostgreSQL数据库服务"
    echo "5. 设置环境变量:"
    echo "   ADMIN_USERNAME=ssss"
    echo "   ADMIN_EMAIL=seventee_0611@qq.com"
    echo "   ADMIN_PASSWORD=ssss123"
    echo "   AUTO_CREATE_ADMIN=true"
    echo ""
    
    read -p "是否已在Railway.app上配置部署? (y/n): " railway_configured
    if [ "$railway_configured" = "y" ]; then
        print_message "✅ Railway.app 部署已配置"
        
        # 如果有Railway URL，测试部署
        if [ -n "$RAILWAY_URL" ]; then
            print_message "测试Railway部署..."
            sleep 30  # 等待部署完成
            
            if curl -f "$RAILWAY_URL" > /dev/null 2>&1; then
                print_message "✅ Railway部署测试成功!"
                echo "🌐 访问地址: $RAILWAY_URL"
            else
                print_warning "⚠️ Railway部署测试失败，请手动检查"
            fi
        fi
    else
        print_warning "请手动在Railway.app上配置部署"
    fi
}

# 部署后验证
post_deployment_verification() {
    print_header "部署后验证"
    
    echo "🔍 请验证以下功能:"
    echo "1. 访问登录页面: /login"
    echo "2. 使用管理员账户登录: ssss / ssss123"
    echo "3. 访问管理后台: /admin_dashboard"
    echo "4. 测试用户管理: /admin/users/"
    echo "5. 检查调试端点: /debug/admin"
    echo ""
    
    echo "🛠️ 如果遇到问题，请使用调试工具:"
    echo "python cloud_login_debug.py https://your-app.onrender.com"
    echo ""
    
    echo "📞 故障排查指南:"
    echo "查看 CLOUD_ADMIN_RECOVERY_GUIDE.md"
}

# 主函数
main() {
    print_header "🚀 ROS2 Wiki 一键部署"
    echo "管理员账户: ssss / ssss123"
    echo "邮箱: seventee_0611@qq.com"
    echo ""
    
    # 执行部署步骤
    check_requirements
    verify_project
    run_tests
    push_to_github
    
    echo ""
    print_message "选择部署平台:"
    echo "1. Render.com (推荐)"
    echo "2. Railway.app"
    echo "3. 两者都部署"
    echo ""
    
    read -p "请选择 (1/2/3): " choice
    
    case $choice in
        1)
            deploy_to_render
            ;;
        2)
            deploy_to_railway
            ;;
        3)
            deploy_to_render
            deploy_to_railway
            ;;
        *)
            print_error "无效选择"
            exit 1
            ;;
    esac
    
    post_deployment_verification
    
    print_header "🎉 部署完成!"
    print_message "您的ROS2 Wiki现在已部署到云端!"
    print_message "管理员账户: ssss / ssss123"
}

# 运行主函数
main "$@"
