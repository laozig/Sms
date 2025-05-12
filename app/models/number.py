#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class NumberStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    RELEASED = "released"

class PhoneNumber(BaseModel):
    """手机号码模型"""
    __tablename__ = 'phone_numbers'
    
    request_id = Column(String(50), unique=True, nullable=False, index=True)
    number = Column(String(20), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    price = Column(Float, default=0.0)
    status = Column(Enum(NumberStatus), default=NumberStatus.PENDING)
    message_count = Column(Integer, default=0)
    
    # 关系
    project = relationship("Project", backref="phone_numbers")
    user = relationship("User", backref="phone_numbers")
    messages = relationship("Message", back_populates="phone_number", cascade="all, delete-orphan")
    
    def to_dict(self):
        """将模型转换为字典"""
        data = super().to_dict()
        data['status'] = self.status.value if self.status else None
        return data
    
    def __repr__(self):
        return f'<PhoneNumber {self.number}>'

class Message(BaseModel):
    """短信消息模型"""
    __tablename__ = 'messages'
    
    phone_number_id = Column(Integer, ForeignKey('phone_numbers.id'))
    sender = Column(String(50))
    content = Column(Text, nullable=False)
    code = Column(String(20), nullable=True)  # 验证码，如果能从消息内容中提取
    
    # 关系
    phone_number = relationship("PhoneNumber", back_populates="messages")
    
    def to_dict(self):
        """将模型转换为字典"""
        data = super().to_dict()
        return data
    
    def __repr__(self):
        return f'<Message {self.id} for {self.phone_number_id}>' 