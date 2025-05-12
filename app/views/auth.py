#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, g
from app.middlewares.auth_middleware import auth_required, generate_jwt_token
from app.services.monitoring import monitor_api
from app.services.user_service import UserService
from app.database import db
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
@monitor_api(endpoint="/api/auth/login")
def login():
    """用户登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误", "code": 400}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "用户名和密码不能为空", "code": 400}), 400
        
        # 调用用户服务进行登录
        success, result = UserService.login(username, password)
        
        if success:
            return jsonify(result)
        else:
            return jsonify({"error": result, "code": 401}), 401
    
    except Exception as e:
        logger.exception("用户登录时发生异常")
        return jsonify({"error": f"登录失败: {str(e)}", "code": 500}), 500

@auth_bp.route('/register', methods=['POST'])
@monitor_api(endpoint="/api/auth/register")
def register():
    """用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误", "code": 400}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({"error": "用户名、邮箱和密码不能为空", "code": 400}), 400
        
        # 基本验证
        if len(username) < 3:
            return jsonify({"error": "用户名长度不能少于3个字符", "code": 400}), 400
        
        if len(password) < 6:
            return jsonify({"error": "密码长度不能少于6个字符", "code": 400}), 400
        
        # 调用用户服务进行注册
        success, result = UserService.register(username, email, password)
        
        if success:
            return jsonify(result)
        else:
            return jsonify({"error": result, "code": 400}), 400
    
    except Exception as e:
        logger.exception("用户注册时发生异常")
        return jsonify({"error": f"注册失败: {str(e)}", "code": 500}), 500

@auth_bp.route('/profile', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/auth/profile")
def get_profile():
    """获取用户个人资料"""
    try:
        user = g.current_user
        
        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "balance": user.balance,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else str(user.created_at)
            }
        })
    
    except Exception as e:
        logger.exception("获取用户个人资料时发生异常")
        return jsonify({"error": f"获取个人资料失败: {str(e)}", "code": 500}), 500

@auth_bp.route('/profile', methods=['PUT'])
@auth_required
@monitor_api(endpoint="/api/auth/profile")
def update_profile():
    """更新用户个人资料"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误", "code": 400}), 400
        
        user_id = g.current_user.id
        
        # 调用用户服务更新资料
        success, result = UserService.update_profile(user_id, data)
        
        if success:
            return jsonify(result)
        else:
            return jsonify({"error": result, "code": 400}), 400
    
    except Exception as e:
        logger.exception("更新用户个人资料时发生异常")
        return jsonify({"error": f"更新个人资料失败: {str(e)}", "code": 500}), 500

@auth_bp.route('/change-password', methods=['POST'])
@auth_required
@monitor_api(endpoint="/api/auth/change-password")
def change_password():
    """修改密码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误", "code": 400}), 400
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({"error": "旧密码和新密码不能为空", "code": 400}), 400
        
        if len(new_password) < 6:
            return jsonify({"error": "新密码长度不能少于6个字符", "code": 400}), 400
        
        user_id = g.current_user.id
        
        # 调用用户服务修改密码
        success, result = UserService.change_password(user_id, old_password, new_password)
        
        if success:
            return jsonify(result)
        else:
            return jsonify({"error": result, "code": 400}), 400
    
    except Exception as e:
        logger.exception("修改密码时发生异常")
        return jsonify({"error": f"修改密码失败: {str(e)}", "code": 500}), 500

@auth_bp.route('/logout', methods=['POST'])
@auth_required
@monitor_api(endpoint="/api/auth/logout")
def logout():
    """用户登出"""
    try:
        # 实际上这里并不需要做什么，因为JWT是无状态的
        # 客户端只需要删除令牌即可
        return jsonify({
            "message": "登出成功"
        })
    
    except Exception as e:
        logger.exception("用户登出时发生异常")
        return jsonify({"error": f"登出失败: {str(e)}", "code": 500}), 500 