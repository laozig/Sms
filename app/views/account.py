#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, g
from app.middlewares.auth_middleware import auth_required
from app.services.monitoring import monitor_api
from app.database import db
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
account_bp = Blueprint('account', __name__)

@account_bp.route('/balance', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/account/balance")
def get_balance():
    """获取用户余额"""
    try:
        user = g.current_user
        
        return jsonify({
            "balance": user.balance
        })
    
    except Exception as e:
        logger.exception("获取用户余额时发生异常")
        return jsonify({"error": f"获取余额失败: {str(e)}", "code": 500}), 500

@account_bp.route('/recharge', methods=['POST'])
@auth_required
@monitor_api(endpoint="/api/account/recharge")
def recharge():
    """充值余额"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误", "code": 400}), 400
        
        amount = data.get('amount')
        if not amount or not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({"error": "充值金额必须为正数", "code": 400}), 400
        
        user = g.current_user
        
        # 模拟充值过程
        session = db.get_session()
        try:
            user = session.query(User).get(user.id)
            user.balance += amount
            session.commit()
            
            return jsonify({
                "message": "充值成功",
                "balance": user.balance,
                "amount": amount
            })
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("充值余额时发生异常")
        return jsonify({"error": f"充值失败: {str(e)}", "code": 500}), 500

@account_bp.route('/transactions', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/account/transactions")
def get_transactions():
    """获取交易记录"""
    try:
        # 获取参数
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        # 限制每页数量
        if per_page > 100:
            per_page = 100
        
        # 模拟交易记录
        import random
        import time
        from datetime import datetime, timedelta
        
        transactions = []
        total = 20  # 模拟总记录数
        
        start_index = (page - 1) * per_page
        end_index = min(start_index + per_page, total)
        
        for i in range(start_index, end_index):
            # 随机生成交易记录
            amount = round(random.uniform(1, 100), 2)
            is_expense = random.choice([True, False])
            days_ago = random.randint(0, 30)
            transaction_time = datetime.now() - timedelta(days=days_ago)
            
            if is_expense:
                amount = -amount
                trans_type = "expense"
                description = "号码消费"
            else:
                trans_type = "recharge"
                description = "账户充值"
            
            transactions.append({
                "id": f"trans_{i}",
                "amount": amount,
                "type": trans_type,
                "description": description,
                "created_at": transaction_time.isoformat()
            })
        
        # 按时间排序
        transactions.sort(key=lambda x: x["created_at"], reverse=True)
        
        return jsonify({
            "items": transactions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        })
    
    except Exception as e:
        logger.exception("获取交易记录时发生异常")
        return jsonify({"error": f"获取交易记录失败: {str(e)}", "code": 500}), 500

@account_bp.route('/statistics', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/account/statistics")
def get_statistics():
    """获取账户统计信息"""
    try:
        user = g.current_user
        
        # 模拟统计数据
        statistics = {
            "total_consumption": 120.5,
            "total_recharge": 200.0,
            "total_numbers": 15,
            "total_messages": 42,
            "last_month_consumption": 45.2,
            "last_month_numbers": 5
        }
        
        return jsonify(statistics)
    
    except Exception as e:
        logger.exception("获取账户统计信息时发生异常")
        return jsonify({"error": f"获取账户统计信息失败: {str(e)}", "code": 500}), 500 