#!/bin/bash

# ROS2 Wiki - 系统服务安装脚本（可选）
# 让网站开机自启动

set -e

echo "⚙️  安装ROS2 Wiki系统服务"
echo "=========================="

# 获取当前用户和路径
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

if [ "$CURRENT_USER" = "root" ]; then
    echo "❌ 请不要使用root用户运行此脚本"
    exit 1
fi

# 创建systemd服务文件
sudo tee /etc/systemd/system/ros2-wiki.service > /dev/null << EOF
[Unit]
Description=ROS2 Wiki Flask Application
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/app.py
Restart=always
RestartSec=3
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# 创建ngrok服务文件
sudo tee /etc/systemd/system/ros2-wiki-ngrok.service > /dev/null << EOF
[Unit]
Description=ROS2 Wiki Ngrok Tunnel
After=network.target ros2-wiki.service
Requires=ros2-wiki.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/local/bin/ngrok http 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
sudo systemctl daemon-reload

echo "✅ 服务文件已创建"
echo ""
echo "🔧 使用方法："
echo "启动服务: sudo systemctl start ros2-wiki"
echo "启动隧道: sudo systemctl start ros2-wiki-ngrok"
echo "开机自启: sudo systemctl enable ros2-wiki ros2-wiki-ngrok"
echo "查看状态: sudo systemctl status ros2-wiki"
echo "查看日志: sudo journalctl -u ros2-wiki -f"
echo "停止服务: sudo systemctl stop ros2-wiki ros2-wiki-ngrok"
echo ""
echo "⚠️  注意: ngrok需要先配置authtoken才能正常工作"