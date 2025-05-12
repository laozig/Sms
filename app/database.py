#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from app.models.base import Base
from app.config import get_config
import threading
import logging

logger = logging.getLogger(__name__)

class Database:
    """数据库管理类，提供连接池和会话管理功能"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        config = get_config()
        
        # 创建数据库引擎，使用连接池
        self.engine = create_engine(
            config.DATABASE_URI,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800  # 30分钟后回收连接
        )
        
        # 创建会话工厂，使用线程绑定的会话
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # 使用scoped_session确保线程安全
        self.Session = scoped_session(self.session_factory)
        
        self._initialized = True
        logger.info(f"Database initialized with URI: {config.DATABASE_URI}")
    
    def create_all(self):
        """创建所有表"""
        logger.info("Creating all database tables...")
        Base.metadata.create_all(self.engine)
    
    def drop_all(self):
        """删除所有表"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(self.engine)
    
    def get_session(self):
        """获取一个会话"""
        return self.Session()
    
    def close_session(self):
        """关闭当前线程的会话"""
        self.Session.remove()

# 单例模式，确保全局只有一个数据库实例
db = Database() 