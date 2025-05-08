import os
import logging
from flask import Flask
from flask_cors import CORS
from app.models import db
from app.config import get_config
from app.routes.auth import auth_bp
from app.routes.projects import projects_bp
from app.routes.numbers import numbers_bp
from app.routes.account import account_bp
from app.routes.statistics import statistics_bp


def create_app(config_name=None):
    """
    创建并配置Flask应用
    
    参数:
        config_name (str): 配置名称
        
    返回:
        Flask: Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    config_obj = get_config()
    app.config.from_object(config_obj)
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化扩展
    db.init_app(app)
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(numbers_bp, url_prefix='/api/numbers')
    app.register_blueprint(account_bp, url_prefix='/api/account')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app 