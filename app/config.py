#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import timedelta

# 应用基础配置
class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_please_change_in_production')
    
    # 数据库配置
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///instance/sms_platform.db')
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt_secret_dev_key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 缓存配置
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 限流配置
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    
    # 异步任务配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # 国际化配置
    BABEL_DEFAULT_LOCALE = 'zh_CN'
    BABEL_TRANSLATION_DIRECTORIES = './translations'

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

# 测试环境配置
class TestingConfig(Config):
    TESTING = True
    DATABASE_URI = 'sqlite:///:memory:'

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    
    # 在生产环境中使用更强的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # 生产环境应使用更严格的限流
    RATELIMIT_DEFAULT = "100 per day, 20 per hour"
    
    # 生产环境应使用Redis进行限流
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# 根据环境变量选择配置
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default']) 