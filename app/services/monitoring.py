#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import threading
import psutil
import datetime
import os
import json
from functools import wraps
from app.config import get_config

logger = logging.getLogger(__name__)

class MetricsCollector:
    """指标收集器，负责收集系统性能指标"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsCollector, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 存储指标数据
        self.metrics = {
            "api_calls": {},  # API调用计数
            "response_times": {},  # 响应时间
            "errors": {},  # 错误计数
            "system": {
                "cpu": 0,
                "memory": 0,
                "disk": 0,
                "start_time": time.time(),
            }
        }
        
        # 创建锁
        self.metrics_lock = threading.Lock()
        
        # 启动背景线程
        self.continue_collecting = True
        self.bg_thread = threading.Thread(target=self._collect_system_metrics, daemon=True)
        self.bg_thread.start()
        
        # 初始化完成标志
        self._initialized = True
        logger.info("指标收集器已初始化")
    
    def _collect_system_metrics(self):
        """收集系统指标的后台线程"""
        while self.continue_collecting:
            try:
                # 收集CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # 收集内存使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # 收集磁盘使用率
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                # 更新系统指标
                with self.metrics_lock:
                    self.metrics["system"]["cpu"] = cpu_percent
                    self.metrics["system"]["memory"] = memory_percent
                    self.metrics["system"]["disk"] = disk_percent
                
                # 休眠一段时间
                time.sleep(60)
            
            except Exception as e:
                logger.error(f"收集系统指标时发生错误: {str(e)}")
                time.sleep(60)
    
    def record_api_call(self, endpoint, method="GET"):
        """记录API调用"""
        with self.metrics_lock:
            # 初始化API调用指标
            if endpoint not in self.metrics["api_calls"]:
                self.metrics["api_calls"][endpoint] = {
                    "total": 0,
                    "methods": {}
                }
            
            # 更新总调用计数
            self.metrics["api_calls"][endpoint]["total"] += 1
            
            # 更新方法调用计数
            if method not in self.metrics["api_calls"][endpoint]["methods"]:
                self.metrics["api_calls"][endpoint]["methods"][method] = 0
            self.metrics["api_calls"][endpoint]["methods"][method] += 1
    
    def record_response_time(self, endpoint, time_ms):
        """记录API响应时间"""
        with self.metrics_lock:
            # 初始化响应时间指标
            if endpoint not in self.metrics["response_times"]:
                self.metrics["response_times"][endpoint] = {
                    "count": 0,
                    "total_ms": 0,
                    "avg_ms": 0,
                    "min_ms": float('inf'),
                    "max_ms": 0,
                    "last_update": time.time()
                }
            
            # 更新响应时间统计
            self.metrics["response_times"][endpoint]["count"] += 1
            self.metrics["response_times"][endpoint]["total_ms"] += time_ms
            self.metrics["response_times"][endpoint]["avg_ms"] = (
                self.metrics["response_times"][endpoint]["total_ms"] / 
                self.metrics["response_times"][endpoint]["count"]
            )
            
            # 更新最小最大值
            if time_ms < self.metrics["response_times"][endpoint]["min_ms"]:
                self.metrics["response_times"][endpoint]["min_ms"] = time_ms
            if time_ms > self.metrics["response_times"][endpoint]["max_ms"]:
                self.metrics["response_times"][endpoint]["max_ms"] = time_ms
                
            # 更新最后更新时间
            self.metrics["response_times"][endpoint]["last_update"] = time.time()
    
    def record_error(self, endpoint, error_type, error_message=None):
        """记录API错误"""
        with self.metrics_lock:
            # 初始化错误指标
            if endpoint not in self.metrics["errors"]:
                self.metrics["errors"][endpoint] = {}
            
            # 更新错误计数
            if error_type not in self.metrics["errors"][endpoint]:
                self.metrics["errors"][endpoint][error_type] = {
                    "count": 0,
                    "last_message": None,
                    "last_time": None
                }
            
            # 更新错误统计
            self.metrics["errors"][endpoint][error_type]["count"] += 1
            self.metrics["errors"][endpoint][error_type]["last_message"] = error_message
            self.metrics["errors"][endpoint][error_type]["last_time"] = time.time()
    
    def get_metrics(self):
        """获取所有指标"""
        with self.metrics_lock:
            # 计算正常运行时间
            uptime = time.time() - self.metrics["system"]["start_time"]
            uptime_formatted = str(datetime.timedelta(seconds=int(uptime)))
            
            # 格式化指标
            formatted_metrics = {
                "api_calls": {},
                "response_times": {},
                "errors": {},
                "system": {
                    "cpu": self.metrics["system"]["cpu"],
                    "memory": self.metrics["system"]["memory"],
                    "disk": self.metrics["system"]["disk"],
                    "uptime": uptime_formatted,
                    "uptime_seconds": int(uptime)
                }
            }
            
            # 格式化API调用指标
            for endpoint, data in self.metrics["api_calls"].items():
                formatted_metrics["api_calls"][endpoint] = data.copy()
            
            # 格式化响应时间指标
            for endpoint, data in self.metrics["response_times"].items():
                formatted_metrics["response_times"][endpoint] = {
                    "count": data["count"],
                    "avg_ms": round(data["avg_ms"], 2),
                    "min_ms": data["min_ms"] if data["min_ms"] != float('inf') else 0,
                    "max_ms": data["max_ms"],
                    "last_update": datetime.datetime.fromtimestamp(data["last_update"]).strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # 格式化错误指标
            for endpoint, errors in self.metrics["errors"].items():
                formatted_metrics["errors"][endpoint] = {}
                for error_type, data in errors.items():
                    formatted_metrics["errors"][endpoint][error_type] = {
                        "count": data["count"],
                        "last_message": data["last_message"],
                        "last_time": datetime.datetime.fromtimestamp(data["last_time"]).strftime('%Y-%m-%d %H:%M:%S') if data["last_time"] else None
                    }
            
            return formatted_metrics
    
    def export_metrics(self):
        """导出指标到文件"""
        with self.metrics_lock:
            # 获取当前时间戳
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 创建指标文件路径
            metrics_dir = os.path.join(os.getcwd(), 'logs')
            if not os.path.exists(metrics_dir):
                os.makedirs(metrics_dir)
            
            metrics_file = os.path.join(metrics_dir, f'metrics_{timestamp}.json')
            
            # 导出指标到文件
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
            
            logger.info(f"指标已导出到文件: {metrics_file}")
            return metrics_file
    
    def stop(self):
        """停止背景线程"""
        self.continue_collecting = False
        if self.bg_thread.is_alive():
            self.bg_thread.join(timeout=5)
        logger.info("指标收集器已停止")

# 创建指标收集器实例
metrics_collector = MetricsCollector()

def monitor_api(endpoint=None):
    """API监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 确定API端点
            nonlocal endpoint
            if endpoint is None:
                # 默认使用函数名作为端点
                endpoint = func.__name__
            
            # 记录API调用
            method = request.method if 'request' in globals() else "UNKNOWN"
            metrics_collector.record_api_call(endpoint, method)
            
            # 记录开始时间
            start_time = time.time()
            
            try:
                # 调用原始函数
                result = func(*args, **kwargs)
                
                # 计算响应时间
                response_time_ms = (time.time() - start_time) * 1000
                metrics_collector.record_response_time(endpoint, response_time_ms)
                
                return result
            
            except Exception as e:
                # 记录错误
                error_type = type(e).__name__
                metrics_collector.record_error(endpoint, error_type, str(e))
                
                # 重新抛出异常
                raise
        
        return wrapper
    return decorator 