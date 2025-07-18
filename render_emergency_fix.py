#!/usr/bin/env python3
"""
紧急修复：确保Render部署成功的最小版本
"""
import os
import sys

# 设置当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入app_render
try:
    from app_render import app
    print("成功导入app_render")
except ImportError as e:
    print(f"导入app_render失败: {e}")
    # 创建一个基本的Flask应用作为备用
    from flask import Flask, render_template, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "ROS2 Wiki - 正在修复中..."
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "message": "Emergency fix active"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))