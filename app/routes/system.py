import time
import psutil
import platform
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from app.utils import token_required, admin_required
from app.models import db
from sqlalchemy import text

system_bp = Blueprint('system', __name__)

# 系统启动时间
START_TIME = time.time()
API_METRICS = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'endpoints': {}
}

# 系统设置
SYSTEM_SETTINGS = {
    'system_name': '接码平台',
    'maintenance_mode': False,
    'default_price': 1.0,
    'min_topup': 10.0,
    'max_topup': 5000.0,
    'sms_timeout': 120,
    'low_balance_alert': 5.0,
    'number_pool_threshold': 100
}

@system_bp.before_request
def before_request():
    """记录API请求"""
    API_METRICS['total_requests'] += 1
    endpoint = request.endpoint
    if endpoint not in API_METRICS['endpoints']:
        API_METRICS['endpoints'][endpoint] = {
            'calls': 0,
            'success': 0,
            'errors': 0
        }
    API_METRICS['endpoints'][endpoint]['calls'] += 1

@system_bp.after_request
def after_request(response):
    """记录API响应结果"""
    endpoint = request.endpoint
    if 200 <= response.status_code < 300:
        API_METRICS['successful_requests'] += 1
        API_METRICS['endpoints'][endpoint]['success'] += 1
    else:
        API_METRICS['failed_requests'] += 1
        API_METRICS['endpoints'][endpoint]['errors'] += 1
    return response

@system_bp.route('/health', methods=['GET', 'POST'])
def health_check():
    """
    系统健康检查API
    
    返回系统健康状态、服务可用性和响应时间
    """
    # 数据库连接检查
    db_status = "healthy"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 系统信息
    uptime = time.time() - START_TIME
    memory = psutil.virtual_memory()
    
    response = {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'uptime': uptime,
        'uptime_formatted': f"{int(uptime // 86400)}天 {int((uptime % 86400) // 3600)}小时 {int((uptime % 3600) // 60)}分钟",
        'version': current_app.config.get('VERSION', '1.0.0'),
        'environment': current_app.config.get('ENV', 'production'),
        'services': {
            'database': db_status,
            'api': 'healthy'
        },
        'system': {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_usage': psutil.cpu_percent(interval=0.1),
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            }
        }
    }
    
    return jsonify(response)

@system_bp.route('/metrics', methods=['GET', 'POST'])
@token_required
def api_metrics():
    """
    获取API使用指标
    
    返回API调用次数、成功率等指标
    """
    # 计算成功率
    success_rate = 0
    if API_METRICS['total_requests'] > 0:
        success_rate = (API_METRICS['successful_requests'] / API_METRICS['total_requests']) * 100
    
    # 获取最常用的端点
    endpoints = []
    for endpoint, data in API_METRICS['endpoints'].items():
        success_rate_endpoint = 0
        if data['calls'] > 0:
            success_rate_endpoint = (data['success'] / data['calls']) * 100
        
        endpoints.append({
            'endpoint': endpoint,
            'calls': data['calls'],
            'success': data['success'],
            'errors': data['errors'],
            'success_rate': success_rate_endpoint
        })
    
    # 按调用次数排序
    endpoints.sort(key=lambda x: x['calls'], reverse=True)
    
    response = {
        'total_requests': API_METRICS['total_requests'],
        'successful_requests': API_METRICS['successful_requests'],
        'failed_requests': API_METRICS['failed_requests'],
        'success_rate': success_rate,
        'endpoints': endpoints[:10]  # 只返回前10个最常用的端点
    }
    
    return jsonify(response)

@system_bp.route('/reset-metrics', methods=['POST'])
@token_required
@admin_required
def reset_metrics():
    """
    重置API指标统计
    
    仅管理员可用
    """
    global API_METRICS
    API_METRICS = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'endpoints': {}
    }
    
    return jsonify({
        'status': 'success',
        'message': 'API指标已重置'
    })

@system_bp.route('/languages', methods=['GET', 'POST'])
def get_languages():
    """
    获取系统支持的语言列表
    """
    languages = [
        {'code': 'zh-CN', 'name': '简体中文', 'default': True},
        {'code': 'en-US', 'name': 'English', 'default': False},
        {'code': 'ja-JP', 'name': '日本語', 'default': False},
        {'code': 'ko-KR', 'name': '한국어', 'default': False}
    ]
    
    return jsonify({
        'languages': languages
    })

@system_bp.route('/settings', methods=['GET'])
@token_required
@admin_required
def get_settings():
    """
    获取系统设置
    
    仅管理员可用
    """
    return jsonify(SYSTEM_SETTINGS)

@system_bp.route('/settings', methods=['POST'])
@token_required
@admin_required
def update_settings():
    """
    更新系统设置
    
    仅管理员可用
    """
    data = request.get_json() or {}
    
    # 更新系统设置
    for key in SYSTEM_SETTINGS:
        if key in data:
            SYSTEM_SETTINGS[key] = data[key]
    
    return jsonify({
        'status': 'success',
        'message': '系统设置已更新',
        'settings': SYSTEM_SETTINGS
    }) 