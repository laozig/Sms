#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from flask import Flask, jsonify, Blueprint
from app.config import get_config
from flask_cors import CORS
from logging.handlers import RotatingFileHandler
import concurrent.futures

# 导入数据库模块
from app.database import db

# 全局线程池
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def create_app(config_name=None):
    """创建应用实例"""
    # 创建应用
    app = Flask(__name__, instance_relative_config=True)
    
    # 加载配置
    config = get_config()
    app.config.from_object(config)
    
    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # 设置日志
    configure_logging(app)
    
    # 配置数据库
    with app.app_context():
        # 创建所有表
        db.create_all()
    
    # 配置CORS
    CORS(app)
    
    # 设置请求日志记录
    from app.middlewares.logging_middleware import setup_request_logging
    setup_request_logging(app)
    
    # 注册蓝图
    from app.views.auth import auth_bp
    from app.views.project import project_bp
    from app.views.number import number_bp
    from app.views.account import account_bp
    from app.views.system import system_bp
    from app.views.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(number_bp, url_prefix='/api/numbers')
    app.register_blueprint(account_bp, url_prefix='/api/account')
    app.register_blueprint(system_bp, url_prefix='/api/system')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # 全局错误处理器
    register_error_handlers(app)
    
    # 添加测试路由
    @app.route('/test')
    def test():
        return "SMS接码平台API系统正常运行中!"
    
    # 从app_instance模块中导入设置应用实例的函数
    from app.app_instance import set_app
    set_app(app)
    
    # 添加启动日志消息
    app.logger.info("SMS接码平台API系统已启动")
    print(f"SMS接码平台API系统已启动，监听端口 {os.environ.get('PORT', 5000)}...")
    
    return app

def configure_logging(app):
    """配置日志记录（仅控制台输出，不保存到文件）"""
    log_level = getattr(app.config, 'LOG_LEVEL', 'INFO')
    
    # 设置格式化器
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(thread)d] %(name)s: %(message)s'
    )
    
    # 只保留控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # 移除所有旧的handler（包括文件handler）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    app.logger.info("日志系统已初始化（仅控制台输出）")

def register_error_handlers(app):
    """注册全局错误处理器"""
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "资源不存在", "code": 404}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "服务器内部错误", "code": 500}), 500

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "不支持的请求方法", "code": 405}), 405

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "请求格式错误", "code": 400}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "未授权访问", "code": 401}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "禁止访问", "code": 403}), 403 