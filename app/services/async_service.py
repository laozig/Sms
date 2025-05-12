#!/usr/bin/env python
# -*- coding: utf-8 -*-

import concurrent.futures
import asyncio
import threading
import logging
import time
import functools
from flask import current_app

logger = logging.getLogger(__name__)

# 全局线程池
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def run_in_thread(func):
    """线程装饰器，在线程池中运行函数"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return thread_pool.submit(func, *args, **kwargs)
    return wrapper

def run_async(func):
    """异步装饰器，使用线程运行函数并立即返回"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

class AsyncTask:
    """异步任务类，用于跟踪异步任务状态"""
    def __init__(self, task_id, description=""):
        self.task_id = task_id
        self.description = description
        self.status = "pending"
        self.result = None
        self.error = None
        self.start_time = time.time()
        self.end_time = None
        self.progress = 0
        self.total = 100
    
    def update_progress(self, progress, total=100):
        """更新任务进度"""
        self.progress = progress
        self.total = total
    
    def complete(self, result=None):
        """标记任务完成"""
        self.status = "completed"
        self.result = result
        self.end_time = time.time()
        self.progress = self.total
    
    def fail(self, error=None):
        """标记任务失败"""
        self.status = "failed"
        self.error = error
        self.end_time = time.time()
    
    def to_dict(self):
        """将任务转换为字典"""
        duration = None
        if self.end_time:
            duration = self.end_time - self.start_time
        
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status,
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": duration,
            "progress": self.progress,
            "total": self.total,
            "progress_percent": int(self.progress / self.total * 100) if self.total else 0
        }

class AsyncTaskManager:
    """异步任务管理器，用于管理和跟踪异步任务"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AsyncTaskManager, cls).__new__(cls)
                cls._instance._tasks = {}
                cls._instance._cleanup_thread = None
                cls._instance._stop_cleanup = False
            return cls._instance
    
    def __init__(self):
        # 启动清理线程
        if self._cleanup_thread is None:
            self._cleanup_thread = threading.Thread(target=self._cleanup_old_tasks)
            self._cleanup_thread.daemon = True
            self._cleanup_thread.start()
    
    def create_task(self, task_id=None, description=""):
        """创建新任务"""
        if task_id is None:
            # 使用时间戳作为任务ID
            task_id = f"task_{int(time.time() * 1000)}"
        
        task = AsyncTask(task_id, description)
        self._tasks[task_id] = task
        return task
    
    def get_task(self, task_id):
        """获取任务"""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self):
        """获取所有任务"""
        return list(self._tasks.values())
    
    def run_task(self, func, task_id=None, description="", *args, **kwargs):
        """创建并运行任务"""
        task = self.create_task(task_id, description)
        
        @run_async
        def _task_wrapper():
            try:
                result = func(*args, **kwargs)
                task.complete(result)
            except Exception as e:
                logger.exception(f"任务执行失败: {str(e)}")
                task.fail(e)
        
        _task_wrapper()
        return task
    
    def _cleanup_old_tasks(self):
        """清理旧任务的后台线程"""
        while not self._stop_cleanup:
            try:
                # 获取当前时间
                now = time.time()
                
                # 清理已完成/已失败且超过1小时的任务
                to_delete = []
                for task_id, task in self._tasks.items():
                    if task.end_time and (now - task.end_time) > 3600:
                        to_delete.append(task_id)
                
                # 删除旧任务
                for task_id in to_delete:
                    del self._tasks[task_id]
                
                # 日志记录已清理的任务数量
                if to_delete:
                    logger.info(f"已清理 {len(to_delete)} 个旧任务")
            
            except Exception as e:
                logger.error(f"清理旧任务时发生错误: {str(e)}")
            
            # 每10分钟运行一次
            time.sleep(600)
    
    def stop(self):
        """停止任务管理器"""
        self._stop_cleanup = True
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)

# 创建任务管理器实例
task_manager = AsyncTaskManager() 