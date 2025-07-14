#!/usr/bin/env python3
"""
WSGI入口文件 - 为Render部署优化
直接导入主应用，避免复杂的导入链
"""

import os

# 设置生产环境
os.environ.setdefault('FLASK_ENV', 'production')

# 直接导入主应用
from app import app

# 确保应用可以被gunicorn找到
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
