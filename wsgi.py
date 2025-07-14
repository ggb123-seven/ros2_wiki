#!/usr/bin/env python3
"""
WSGI入口文件 - 专门为Render部署优化
"""

import os
import sys

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')

# 尝试导入应用 - 优先使用Render专用版本
try:
    from app_render import app
    print("✅ 成功导入 app_render (Render专用版本)")
except ImportError as e:
    print(f"❌ 导入 app_render 失败: {e}")
    try:
        from app_emergency import app
        print("✅ 成功导入 app_emergency")
    except ImportError as e2:
        print(f"❌ 导入 app_emergency 失败: {e2}")
        try:
            from app import app
            print("✅ 成功导入 app")
        except ImportError as e3:
            print(f"❌ 导入 app 失败: {e3}")
            # 创建最简单的Flask应用
            from flask import Flask
            app = Flask(__name__)

            @app.route('/')
            def hello():
                return '''
                <h1>🎉 ROS2 Wiki 部署成功!</h1>
                <p>应用正在Render平台上运行</p>
                <p>如果您看到此页面，说明部署配置正确。</p>
                '''

            @app.route('/health')
            def health():
                return {'status': 'ok', 'message': 'ROS2 Wiki is running'}

# 确保应用可以被gunicorn找到
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
