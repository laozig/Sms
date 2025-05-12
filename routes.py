#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import jsonify, request
import time
import random
from datetime import datetime, timedelta
import uuid
import re

# 从app_instance导入app，从app导入admin_bp
from app_instance import app
from app import admin_bp
from mock_server import db, auth_required, admin_required
import models

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def make_error_response(message, code):
    return jsonify({
        "error": message,
        "code": code,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), code

# 用户认证API
@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.json
        if not data:
            return make_error_response("无效的请求数据", 400)

        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return make_error_response("用户名和密码不能为空", 400)
        
        # 查找用户
        for user_id, user in db["users"].items():
            if user["username"] == username and user["password"] == password:
                token = str(uuid.uuid4())
                return jsonify({
                    "code": 200,
                    "data": {
                        "token": token,
                        "user": {
                            "id": user_id,
                            "username": user["username"],
                            "email": user["email"],
                            "is_admin": user.get("is_admin", False)
                        }
                    }
                })
        
        return make_error_response("用户名或密码错误", 401)
    except Exception as e:
        return make_error_response(f"服务器错误: {str(e)}", 500)

# 注册API
@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.json
        if not data:
            return make_error_response("无效的请求数据", 400)

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        
        # 参数验证
        if not all([username, email, password]):
            return make_error_response("所有字段都是必填的", 400)
            
        if len(username) < 3 or len(username) > 20:
            return make_error_response("用户名长度必须在3-20个字符之间", 400)
            
        if not validate_email(email):
            return make_error_response("无效的邮箱格式", 400)
            
        if len(password) < 6:
            return make_error_response("密码长度必须至少为6个字符", 400)
        
        # 检查用户名是否已存在
        for user in db["users"].values():
            if user["username"].lower() == username.lower():
                return make_error_response("用户名已存在", 400)
            if user["email"].lower() == email.lower():
                return make_error_response("邮箱已被注册", 400)
        
        # 创建新用户
        user_id = str(uuid.uuid4())
        db["users"][user_id] = {
            "id": user_id,
            "username": username,
            "email": email,
            "password": password,  # 明文存储密码
            "is_admin": False,
            "balance": 10.0,  # 新用户初始余额
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        token = str(uuid.uuid4())
        return jsonify({
            "code": 200,
            "data": {
                "token": token,
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "is_admin": False
                }
            }
        })
    except Exception as e:
        return make_error_response(f"服务器错误: {str(e)}", 500)

# 健康检查API
@app.route("/api/system/health", methods=["GET"])
def system_health():
    try:
        return jsonify({
            "code": 200,
            "data": {
                "status": "ok",
                "version": "1.0.0",
                "uptime": int(time.time()),
                "services": {
                    "database": "ok",
                    "api": "ok"
                }
            }
        })
    except Exception as e:
        return make_error_response(f"服务器错误: {str(e)}", 500)

# 指标API
@app.route("/api/system/metrics", methods=["GET"])
@auth_required
def system_metrics():
    try:
        return jsonify({
            "code": 200,
            "data": {
                "api_calls": {
                    "today": random.randint(100, 1000),
                    "total": random.randint(10000, 100000)
                },
                "active_users": random.randint(10, 100),
                "active_sessions": random.randint(5, 50),
                "response_time_ms": random.randint(50, 200)
            }
        })
    except Exception as e:
        return make_error_response(f"服务器错误: {str(e)}", 500)

# 支持的语言
@app.route("/api/system/languages", methods=["GET"])
def system_languages():
    try:
        return jsonify({
            "code": 200,
            "data": {
                "available": ["zh-CN", "en-US", "ru-RU"],
                "default": "zh-CN"
            }
        })
    except Exception as e:
        return make_error_response(f"服务器错误: {str(e)}", 500) 