#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Float, Boolean
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.base import BaseModel

class User(BaseModel):
    """用户模型"""
    __tablename__ = 'users'
    
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    balance = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    @property
    def password(self):
        """密码属性不可读"""
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """设置密码时，自动进行哈希处理"""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """验证密码是否正确"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """将用户模型转换为字典，不包含敏感数据"""
        data = super().to_dict()
        # 移除敏感数据
        data.pop('password_hash', None)
        return data
    
    def __repr__(self):
        return f'<User {self.username}>' 