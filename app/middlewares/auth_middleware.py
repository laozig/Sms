#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jwt
import time
from functools import wraps
from flask import request, jsonify, current_app, g
from app.database import db
from app.models.user import User
from app.services.cache_service import cache, cached
import logging

logger = logging.getLogger(__name__)

def get_token_from_request():
    """从请求中提取认证令牌"""
    # 从请求头中获取
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    # 从查询参数中获取
    token = request.args.get("token")
    if token:
        return token
    
    # 从表单中获取
    token = request.form.get("token")
    if token:
        return token
    
    # 从JSON请求体中获取
    try:
        json_data = request.get_json(silent=True)
        if json_data and "token" in json_data:
            return json_data["token"]
    except:
        pass
    
    return None

def generate_jwt_token(user_id, username, is_admin=False, expiry=3600):
    """生成JWT令牌"""
    payload = {
        "user_id": user_id,
        "username": username,
        "is_admin": is_admin,
        "exp": int(time.time()) + expiry
    }
    
    token = jwt.encode(
        payload,
        current_app.config.get("JWT_SECRET_KEY", "dev-jwt-secret"),
        algorithm="HS256"
    )
    
    return token

@cached(ttl=300)  # 缓存5分钟
def validate_token(token):
    """验证令牌并返回用户ID"""
    if not token:
        return None
    
    try:
        # 解码令牌
        payload = jwt.decode(
            token,
            current_app.config.get("JWT_SECRET_KEY", "dev-jwt-secret"),
            algorithms=["HS256"]
        )
        
        # 获取用户ID
        user_id = payload.get("user_id")
        if not user_id:
            logger.warning(f"令牌缺少用户ID: {token[:10]}...")
            return None
        
        return user_id
    
    except jwt.ExpiredSignatureError:
        logger.warning(f"令牌已过期: {token[:10]}...")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"无效的令牌: {token[:10]}..., 错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"验证令牌时发生错误: {str(e)}")
        return None

def auth_required(func):
    """需要用户认证的API装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 获取令牌
        token = get_token_from_request()
        
        # 验证令牌
        user_id = validate_token(token)
        if not user_id:
            return jsonify({"error": "未授权访问", "code": 401}), 401
        
        # 从数据库获取用户
        session = db.get_session()
        try:
            user = session.query(User).get(user_id)
            if not user or not user.is_active:
                return jsonify({"error": "用户不存在或已禁用", "code": 401}), 401
            
            # 将用户存储在g对象中，以便视图函数访问
            g.current_user = user
            
            # 调用原始视图函数
            return func(*args, **kwargs)
        finally:
            db.close_session()
    
    return wrapper

def admin_required(func):
    """需要管理员权限的API装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 获取令牌
        token = get_token_from_request()
        
        # 验证令牌
        user_id = validate_token(token)
        if not user_id:
            return jsonify({"error": "未授权访问", "code": 401}), 401
        
        # 从数据库获取用户并检查管理员权限
        session = db.get_session()
        try:
            user = session.query(User).get(user_id)
            if not user or not user.is_active:
                return jsonify({"error": "用户不存在或已禁用", "code": 401}), 401
            
            if not user.is_admin:
                return jsonify({"error": "需要管理员权限", "code": 403}), 403
            
            # 将用户存储在g对象中，以便视图函数访问
            g.current_user = user
            
            # 调用原始视图函数
            return func(*args, **kwargs)
        finally:
            db.close_session()
    
    return wrapper 