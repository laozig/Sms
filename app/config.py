import os
from datetime import timedelta

class Config:
    """应用配置类"""
    # 密钥配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-replace-in-production'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///sms_platform.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-replace-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 接码平台API配置
    SMS_API_BASE_URL = os.environ.get('SMS_API_BASE_URL') or 'https://api.example-sms-provider.com'
    SMS_API_KEY = os.environ.get('SMS_API_KEY') or 'your-api-key'
    # 是否使用模拟API（用于本地测试）
    USE_MOCK_API = os.environ.get('USE_MOCK_API', 'True').lower() in ('true', '1', 't')
    
    # 分页配置
    ITEMS_PER_PAGE = 10
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_sms_platform.db'
    # 开发环境下默认使用模拟API
    USE_MOCK_API = True


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_sms_platform.db'
    # 测试环境下默认使用模拟API
    USE_MOCK_API = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境请使用环境变量设置这些值
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SMS_API_BASE_URL = os.environ.get('SMS_API_BASE_URL')
    SMS_API_KEY = os.environ.get('SMS_API_KEY')


# 配置映射
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """获取当前环境的配置"""
    env = os.environ.get('FLASK_ENV') or 'default'
    return config_by_name[env] 