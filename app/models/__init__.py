#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models.base import Base, BaseModel
from app.models.user import User
from app.models.project import Project
from app.models.number import PhoneNumber, Message, NumberStatus

# 在这里导入所有模型，确保在初始化数据库时能够创建所有表
__all__ = [
    'Base',
    'BaseModel',
    'User',
    'Project',
    'PhoneNumber',
    'Message',
    'NumberStatus'
] 