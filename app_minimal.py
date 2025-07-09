#!/usr/bin/env python3
"""
最小化Flask应用 - 用于诊断Render部署问题
"""

import os
import sys

def main():
    print("=== ROS2 Wiki 部署诊断 ===")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    print(f"环境变量:")
    
    # 检查关键环境变量
    env_vars = [
        'FLASK_ENV', 'SECRET_KEY', 'DATABASE_URL', 
        'ADMIN_USERNAME', 'ADMIN_PASSWORD', 'PORT'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NOT_SET')
        # 隐藏敏感信息
        if 'PASSWORD' in var or 'SECRET' in var:
            value = '*****' if value != 'NOT_SET' else 'NOT_SET'
        print(f"  {var}: {value}")
    
    # 测试基本导入
    print("\n=== 测试导入 ===")
    try:
        import flask
        print("✓ Flask 导入成功")
        print(f"  Flask版本: {flask.__version__}")
    except ImportError as e:
        print(f"✗ Flask 导入失败: {e}")
        return 1
    
    try:
        import psycopg2
        print("✓ psycopg2 导入成功")
    except ImportError as e:
        print(f"✗ psycopg2 导入失败: {e}")
        return 1
    
    # 测试Flask应用创建
    print("\n=== 测试Flask应用 ===")
    try:
        from flask import Flask
        app = Flask(__name__)
        
        # 基本配置
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-key')
        
        @app.route('/')
        def home():
            return '''
            <h1>🎉 ROS2 Wiki 部署成功!</h1>
            <p>最小化版本正在运行</p>
            <p>下一步: 启用完整功能</p>
            '''
        
        @app.route('/health')
        def health():
            return {'status': 'ok', 'message': '应用运行正常'}
        
        print("✓ Flask应用创建成功")
        
        # 启动服务器
        port = int(os.environ.get('PORT', 5000))
        print(f"\n🚀 启动服务器 - 端口: {port}")
        
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        print(f"✗ Flask应用创建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())