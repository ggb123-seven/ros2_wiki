#!/usr/bin/env python3
"""
ROS2 Wiki Enhanced Server - Production Startup Script
适用于Render.com部署的启动脚本
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并运行服务器
from enhanced_server import main

if __name__ == "__main__":
    # 获取Render提供的端口，默认8000
    port = int(os.environ.get('PORT', 8000))
    
    # 修改主函数以使用环境变量端口
    print(f"🚀 Starting ROS2 Wiki on port {port}")
    
    # 由于enhanced_server.py中端口是硬编码的，我们需要动态修改
    import enhanced_server
    enhanced_server.PORT = port
    
    # 启动服务器
    main()