#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import logging
import threading
import hashlib
import pickle
from functools import wraps
from app.config import get_config

logger = logging.getLogger(__name__)

class CacheBackend:
    """缓存后端基类"""
    def get(self, key):
        raise NotImplementedError
    
    def set(self, key, value, ttl=None):
        raise NotImplementedError
    
    def delete(self, key):
        raise NotImplementedError
    
    def flush(self):
        raise NotImplementedError

class MemoryCache(CacheBackend):
    """内存缓存后端"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MemoryCache, cls).__new__(cls)
                cls._instance._cache = {}
                cls._instance._expires = {}
            return cls._instance
    
    def get(self, key):
        """获取缓存值"""
        # 检查过期
        if key in self._expires and self._expires[key] < time.time():
            self.delete(key)
            return None
            
        # 返回值
        return self._cache.get(key)
    
    def set(self, key, value, ttl=None):
        """设置缓存值"""
        self._cache[key] = value
        
        # 设置过期时间
        if ttl is not None:
            self._expires[key] = time.time() + ttl
    
    def delete(self, key):
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expires:
            del self._expires[key]
    
    def flush(self):
        """清空缓存"""
        self._cache.clear()
        self._expires.clear()

class RedisCache(CacheBackend):
    """Redis缓存后端"""
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def get(self, key):
        """获取缓存值"""
        value = self.redis.get(key)
        if value:
            return pickle.loads(value)
        return None
    
    def set(self, key, value, ttl=None):
        """设置缓存值"""
        value_bytes = pickle.dumps(value)
        if ttl is not None:
            self.redis.setex(key, ttl, value_bytes)
        else:
            self.redis.set(key, value_bytes)
    
    def delete(self, key):
        """删除缓存值"""
        self.redis.delete(key)
    
    def flush(self):
        """清空缓存"""
        self.redis.flushdb()

class CacheService:
    """缓存服务，提供统一的缓存接口"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CacheService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        config = get_config()
        cache_type = getattr(config, 'CACHE_TYPE', 'SimpleCache')
        
        if cache_type == 'RedisCache':
            try:
                import redis
                redis_url = getattr(config, 'CACHE_REDIS_URL', 'redis://localhost:6379/0')
                redis_client = redis.from_url(redis_url)
                self.backend = RedisCache(redis_client)
                logger.info(f"使用Redis缓存后端: {redis_url}")
            except ImportError:
                logger.warning("找不到redis库，回退到内存缓存")
                self.backend = MemoryCache()
        else:
            self.backend = MemoryCache()
            logger.info("使用内存缓存后端")
        
        self.default_ttl = getattr(config, 'CACHE_DEFAULT_TIMEOUT', 300)
        self._initialized = True
    
    def get(self, key):
        """获取缓存值"""
        return self.backend.get(key)
    
    def set(self, key, value, ttl=None):
        """设置缓存值"""
        if ttl is None:
            ttl = self.default_ttl
        return self.backend.set(key, value, ttl)
    
    def delete(self, key):
        """删除缓存值"""
        return self.backend.delete(key)
    
    def flush(self):
        """清空缓存"""
        return self.backend.flush()

    def cache_key(self, *args, **kwargs):
        """生成缓存键"""
        # 创建一个包含所有参数的字符串
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_str = ":".join(key_parts)
        
        # 使用MD5哈希生成固定长度的键
        return hashlib.md5(key_str.encode()).hexdigest()

# 创建缓存实例
cache = CacheService()

def cached(ttl=None):
    """缓存装饰器，用于缓存函数返回值"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"cache:{func.__module__}:{func.__name__}:{cache.cache_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 调用原始函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        return wrapper
    return decorator 