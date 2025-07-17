"""
重构后的ROS2 Wiki应用
米醋电子工作室 - SuperClaude模块化重构
"""

from flask import Flask
from flask_login import LoginManager
import os

# 全局对象
login_manager = LoginManager()

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    from config import config
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    # 注册蓝图
    from .routes import auth_bp, main_bp, admin_bp, api_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 注册错误处理
    from .error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # 初始化数据库
    from .models import init_db
    with app.app_context():
        init_db()
    
    return app