#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request
from app.middlewares.auth_middleware import admin_required
from app.services.monitoring import metrics_collector, monitor_api
import time
import random
import platform
import os
import psutil
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
system_bp = Blueprint('system', __name__)

@system_bp.route('/health', methods=['GET'])
@monitor_api(endpoint="/api/system/health")
def system_health():
    """系统健康检查API"""
    try:
        # 获取系统信息
        system_info = {
            "status": "ok",
            "version": "1.0.0",
            "uptime": int(time.time() - psutil.boot_time()),
            "services": {
                "database": "ok",
                "api": "ok"
            },
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": os.cpu_count(),
                "memory_total_mb": round(psutil.virtual_memory().total / (1024 * 1024))
            }
        }
        
        return jsonify(system_info)
    
    except Exception as e:
        logger.exception("获取系统健康信息时发生异常")
        return jsonify({"error": f"获取系统健康信息失败: {str(e)}", "code": 500}), 500

@system_bp.route('/metrics', methods=['GET'])
@admin_required
@monitor_api(endpoint="/api/system/metrics")
def system_metrics():
    """系统指标API，需要管理员权限"""
    try:
        # 获取指标收集器的指标
        metrics = metrics_collector.get_metrics()
        
        # 添加一些附加信息
        metrics["timestamp"] = int(time.time())
        
        return jsonify(metrics)
    
    except Exception as e:
        logger.exception("获取系统指标时发生异常")
        return jsonify({"error": f"获取系统指标失败: {str(e)}", "code": 500}), 500

@system_bp.route('/languages', methods=['GET'])
@monitor_api(endpoint="/api/system/languages")
def system_languages():
    """支持的语言API"""
    try:
        languages = {
            "available": ["zh-CN", "en-US", "ru-RU"],
            "default": "zh-CN"
        }
        
        return jsonify(languages)
    
    except Exception as e:
        logger.exception("获取支持的语言时发生异常")
        return jsonify({"error": f"获取支持的语言失败: {str(e)}", "code": 500}), 500

@system_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
@monitor_api(endpoint="/api/system/settings")
def system_settings():
    """系统设置API，需要管理员权限"""
    try:
        if request.method == 'GET':
            # 获取系统设置
            settings = {
                "system_name": "SMS接码平台",
                "maintenance_mode": False,
                "registration_enabled": True,
                "default_user_balance": 0.0,
                "price_discount": 1.0,
                "notification_enabled": True
            }
            
            return jsonify(settings)
        
        elif request.method == 'POST':
            # 更新系统设置
            data = request.get_json()
            if not data:
                return jsonify({"error": "请求数据格式错误", "code": 400}), 400
            
            # 验证设置有效性...
            
            # 返回更新后的设置
            return jsonify({
                "message": "系统设置已更新",
                "settings": data
            })
    
    except Exception as e:
        logger.exception("操作系统设置时发生异常")
        return jsonify({"error": f"操作系统设置失败: {str(e)}", "code": 500}), 500 