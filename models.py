#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
import uuid
from dataclasses import dataclass, field

class ValidationError(Exception):
    """验证错误异常类"""
    pass

@dataclass
class PhoneRequest:
    """手机号请求模型，用于存储和管理用户获取的手机号码"""
    id: str = field(default_factory=lambda: f"req_{uuid.uuid4()}")
    user_id: str = field(default=None)
    project_id: int = field(default=None)
    number: Optional[str] = field(default=None)
    status: str = field(default="pending")
    created_at: datetime = field(default_factory=datetime.now)
    sms_list: List['SMS'] = field(default_factory=list)

    def __post_init__(self):
        """验证数据完整性"""
        if self.user_id is None:
            raise ValidationError("user_id 不能为空")
        if self.project_id is None:
            raise ValidationError("project_id 不能为空")
        if self.number and not self._is_valid_phone(self.number):
            raise ValidationError("无效的手机号格式")
        if self.status not in ["pending", "active", "expired", "cancelled"]:
            raise ValidationError("无效的状态值")

    @staticmethod
    def _is_valid_phone(number: str) -> bool:
        """验证手机号格式"""
        return bool(re.match(r'^\+?1?\d{9,15}$', number))

    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典，用于API响应"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "number": self.number,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "sms_count": len(self.sms_list),
            "sms_list": [sms.to_dict() for sms in self.sms_list]
        }

@dataclass
class SMS:
    """短信消息模型，用于存储和管理接收到的短信"""
    id: str = field(default_factory=lambda: f"sms_{uuid.uuid4()}")
    request_id: Optional[str] = field(default=None)
    content: Optional[str] = field(default=None)
    sender: Optional[str] = field(default=None)
    received_at: datetime = field(default_factory=datetime.now)
    verification_code: Optional[str] = None

    def __post_init__(self):
        """验证数据完整性并提取验证码"""
        if self.request_id is None:
            raise ValidationError("request_id 不能为空")
        if self.content is None:
            raise ValidationError("content 不能为空")
        if self.sender is None:
            raise ValidationError("sender 不能为空")
        self.verification_code = extract_verification_code(self.content)

    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典，用于API响应"""
        return {
            "id": self.id,
            "request_id": self.request_id,
            "content": self.content,
            "sender": self.sender,
            "received_at": self.received_at.strftime("%Y-%m-%d %H:%M:%S"),
            "verification_code": self.verification_code
        }

def extract_verification_code(sms_content: Optional[str]) -> Optional[str]:
    """
    从短信内容中提取验证码
    支持多种常见验证码格式
    
    Args:
        sms_content: 短信内容
        
    Returns:
        提取出的验证码，如果未找到则返回None
        
    Raises:
        ValidationError: 当短信内容为空时
    """
    if not sms_content:
        raise ValidationError("短信内容不能为空")
        
    # 常见验证码模式
    patterns = [
        r'验证码[^\d]*(\d{4,6})',  # 验证码 123456
        r'验证码是[^\d]*(\d{4,6})',  # 验证码是 123456
        r'验证码为[^\d]*(\d{4,6})',  # 验证码为 123456
        r'code[^\d]*(\d{4,6})',  # code 123456
        r'码[^\d]*(\d{4,6})',  # 码 123456
        r'代码[^\d]*(\d{4,6})',  # 代码 123456
        r'口令[^\d]*(\d{4,6})',  # 口令 123456
        r'密码[^\d]*(\d{4,6})',  # 密码 123456
        r'(\d{4,6})[^\d]*(验证|校验)',  # 123456 验证
        r'[code|码].*?(\d{4,6})',  # 任何包含code或码后跟数字的形式
        r'(\d{4,6})',  # 如果上述都没匹配到，尝试匹配4-6位数字
    ]

    for pattern in patterns:
        match = re.search(pattern, sms_content)
        if match:
            return match.group(1)
    
    return None 