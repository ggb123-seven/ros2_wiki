#!/bin/bash

# ROS2 Wiki - 简化版ngrok配置脚本
# 不需要sudo权限，安装到本地目录

set -e

echo "🚀 ROS2 Wiki - 简化版公网访问配置"
echo "================================="

# 检查系统架构
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
elif [ "$ARCH" = "aarch64" ]; then
    NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz"
else
    echo "❌ 不支持的系统架构: $ARCH"
    exit 1
fi

# 检查ngrok是否已安装
if [ -f "./ngrok" ]; then
    echo "✅ ngrok已安装，跳过下载"
else
    echo "📥 1. 下载ngrok..."
    wget -q --show-progress "$NGROK_URL" -O ngrok.tgz
    echo "📦 2. 解压ngrok..."
    tar xzf ngrok.tgz
    rm ngrok.tgz
    chmod +x ngrok
    echo "✅ ngrok下载完成"
fi

echo "🔑 3. 配置ngrok认证..."
echo ""
echo "请按以下步骤获取您的免费token："
echo "1. 访问 https://dashboard.ngrok.com/signup"
echo "2. 使用Google/GitHub账号注册（完全免费）"
echo "3. 访问 https://dashboard.ngrok.com/get-started/your-authtoken"
echo "4. 复制您的authtoken"
echo ""
read -p "请输入您的ngrok authtoken: " AUTHTOKEN

if [ -z "$AUTHTOKEN" ]; then
    echo "❌ 未输入authtoken，请重新运行脚本"
    exit 1
fi

# 配置authtoken
./ngrok config add-authtoken "$AUTHTOKEN"
echo "✅ authtoken配置完成"

echo "🐍 4. 检查Python依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ 未找到requirements.txt，请确保在ros2_wiki目录下运行"
    exit 1
fi

# 安装Python依赖
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 安装Python依赖..."
    pip3 install -r requirements.txt
else
    echo "✅ Python依赖已安装"
fi

echo "🗄️ 5. 初始化数据库..."
if [ ! -f "ros2_wiki.db" ]; then
    python3 init_sample_data.py
    echo "✅ 示例数据已初始化"
else
    echo "✅ 数据库已存在"
fi

echo ""
echo "🎉 配置完成！"
echo "=================="
echo "现在您可以使用以下命令启动公网访问："
echo ""
echo "  ./start_public_simple.sh"
echo ""
echo "或者手动启动："
echo "  python3 app.py &"
echo "  ./ngrok http 5000"
echo ""
echo "📱 默认账户："
echo "  管理员: admin / admin123"
echo "  用户: ros2_learner / user123"