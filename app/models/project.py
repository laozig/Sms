#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Float, Boolean, Text
from app.models.base import BaseModel

class Project(BaseModel):
    """项目模型"""
    __tablename__ = 'projects'
    
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0.0, nullable=False)
    success_rate = Column(Float, default=0.0)
    available = Column(Boolean, default=True)
    is_exclusive = Column(Boolean, default=False)
    exclusive_id = Column(String(50), nullable=True)
    
    def to_dict(self):
        """将模型转换为字典"""
        data = super().to_dict()
        return data
    
    def __repr__(self):
        return f'<Project {self.name}>' 