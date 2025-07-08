#!/bin/bash

# ROS2 Wiki - ngrok自动化配置脚本
# 用于快速配置公网访问

set -e

echo "🚀 ROS2 Wiki - 自动配置公网访问"
echo "=================================="

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

# 创建临时目录
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "📥 1. 下载ngrok..."
if command -v ngrok >/dev/null 2>&1; then
    echo "✅ ngrok已安装，跳过下载"
else
    wget -q --show-progress "$NGROK_URL" -O ngrok.tgz
    echo "📦 2. 解压ngrok..."
    tar xzf ngrok.tgz
    echo "🔧 3. 安装ngrok到系统..."
    sudo mv ngrok /usr/local/bin/
    sudo chmod +x /usr/local/bin/ngrok
fi

# 返回项目目录
cd - > /dev/null

echo "🔑 4. 配置ngrok认证..."
echo "请访问 https://dashboard.ngrok.com/get-started/your-authtoken 获取您的免费token"
echo "然后输入您的ngrok authtoken:"
read -p "Authtoken: " AUTHTOKEN

if [ -z "$AUTHTOKEN" ]; then
    echo "❌ 未输入authtoken，请重新运行脚本"
    exit 1
fi

# 配置authtoken
ngrok config add-authtoken "$AUTHTOKEN"
echo "✅ authtoken配置完成"

echo "🐍 5. 检查Python依赖..."
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

echo "🗄️ 6. 初始化数据库..."
if [ ! -f "ros2_wiki.db" ]; then
    python3 init_sample_data.py
    echo "✅ 示例数据已初始化"
else
    echo "✅ 数据库已存在"
fi

# 清理临时文件
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 配置完成！"
echo "=================="
echo "现在您可以使用以下命令启动公网访问："
echo ""
echo "  ./start_public.sh"
echo ""
echo "或者手动启动："
echo "  python3 app.py &"
echo "  ngrok http 5000"
echo ""
echo "📱 默认账户："
echo "  管理员: admin / admin123"
echo "  用户: ros2_learner / user123"