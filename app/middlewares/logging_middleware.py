#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import threading
import json
import uuid
from functools import wraps
from flask import request, g, current_app
from app.services.monitoring import metrics_collector
import traceback

logger = logging.getLogger(__name__)

def setup_request_logging(app):
    """设置请求日志记录"""
    @app.before_request
    def before_request():
        """在请求处理之前执行"""
        # 生成请求ID
        g.request_id = str(uuid.uuid4())
        
        # 记录请求开始时间
        g.start_time = time.time()
        
        # 记录请求信息
        logger.info(f"请求开始 [{g.request_id}]: {request.method} {request.path}")
        
        # 记录请求头和参数
        if current_app.debug:
            headers = {k: v for k, v in request.headers.items()}
            args = request.args.to_dict() if request.args else {}
            form = request.form.to_dict() if request.form else {}
            try:
                json_data = request.get_json(silent=True) or {}
            except:
                json_data = {}
            
            logger.debug(
                f"请求详情 [{g.request_id}]: "
                f"Headers: {json.dumps(headers, ensure_ascii=False)}, "
                f"Args: {json.dumps(args, ensure_ascii=False)}, "
                f"Form: {json.dumps(form, ensure_ascii=False)}, "
                f"JSON: {json.dumps(json_data, ensure_ascii=False)}"
            )
        
        # 记录API调用指标
        metrics_collector.record_api_call(request.path, request.method)
    
    @app.after_request
    def after_request(response):
        """在请求处理之后执行"""
        # 计算请求处理时间
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            # 添加处理时间到响应头
            response.headers['X-Processing-Time'] = f"{duration_ms:.2f}ms"
            
            # 获取请求ID
            request_id = getattr(g, 'request_id', 'unknown')
            response.headers['X-Request-ID'] = request_id
            
            # 记录请求处理完成
            logger.info(
                f"请求完成 [{request_id}]: {request.method} {request.path} "
                f"- 状态码: {response.status_code}, 耗时: {duration_ms:.2f}ms"
            )
            
            # 记录响应内容
            if current_app.debug and response.content_type == 'application/json':
                try:
                    resp_data = json.loads(response.get_data(as_text=True))
                    logger.debug(f"响应内容 [{request_id}]: {json.dumps(resp_data, ensure_ascii=False)}")
                except:
                    pass
            
            # 记录API响应时间指标
            metrics_collector.record_response_time(request.path, duration_ms)
            
            # 如果是错误响应，记录错误指标
            if response.status_code >= 400:
                error_type = f"HTTP{response.status_code}"
                metrics_collector.record_error(request.path, error_type)
        
        return response
    
    @app.teardown_request
    def teardown_request(exception=None):
        """在请求完成后执行，无论是否发生异常"""
        if exception:
            # 获取请求ID
            request_id = getattr(g, 'request_id', 'unknown')
            
            # 记录异常信息
            logger.error(
                f"请求异常 [{request_id}]: {request.method} {request.path} "
                f"- 异常: {str(exception)}"
            )
            
            # 记录异常堆栈
            if current_app.debug:
                logger.error(f"异常堆栈 [{request_id}]:\n{traceback.format_exc()}")
            
            # 记录API错误指标
            error_type = type(exception).__name__
            metrics_collector.record_error(request.path, error_type, str(exception))

def log_function_call(func=None, level=logging.INFO):
    """函数调用日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成调用ID
            call_id = str(uuid.uuid4())
            
            # 记录函数调用开始
            func_name = f"{func.__module__}.{func.__name__}"
            arg_str = ", ".join([repr(a) for a in args] + [f"{k}={repr(v)}" for k, v in kwargs.items()])
            logger.log(level, f"函数调用开始 [{call_id}]: {func_name}({arg_str})")
            
            # 记录开始时间
            start_time = time.time()
            
            try:
                # 调用原始函数
                result = func(*args, **kwargs)
                
                # 计算函数执行时间
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录函数调用完成
                logger.log(level, f"函数调用完成 [{call_id}]: {func_name} - 耗时: {duration_ms:.2f}ms")
                
                return result
            
            except Exception as e:
                # 计算函数执行时间
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录函数调用异常
                logger.error(
                    f"函数调用异常 [{call_id}]: {func_name} - 耗时: {duration_ms:.2f}ms, 异常: {str(e)}"
                )
                
                # 记录异常堆栈
                logger.error(f"异常堆栈 [{call_id}]:\n{traceback.format_exc()}")
                
                # 重新抛出异常
                raise
        
        return wrapper
    
    # 处理直接调用和参数调用两种情况
    if func is None:
        return decorator
    else:
        return decorator(func) 