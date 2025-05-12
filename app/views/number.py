#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, g
from app.middlewares.auth_middleware import auth_required
from app.services.monitoring import monitor_api
from app.database import db
from app.models.project import Project
from app.models.number import PhoneNumber, Message, NumberStatus
from app.services.async_service import task_manager
import uuid
import random
import time
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# 创建蓝图
number_bp = Blueprint('number', __name__)

@number_bp.route('/get', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/numbers/get")
def get_number():
    """获取手机号码"""
    try:
        # 获取项目ID
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({"error": "项目ID不能为空", "code": 400}), 400
        
        try:
            project_id = int(project_id)
        except ValueError:
            return jsonify({"error": "项目ID必须为整数", "code": 400}), 400
        
        session = db.get_session()
        try:
            # 查询项目
            project = session.query(Project).get(project_id)
            if not project:
                return jsonify({"error": "项目不存在", "code": 404}), 404
            
            # 检查项目可用性
            if not project.available:
                return jsonify({"error": "项目不可用", "code": 403}), 403
            
            # 检查用户余额
            user = g.current_user
            if user.balance < project.price:
                return jsonify({"error": "余额不足", "code": 403}), 403
            
            # 生成请求ID
            request_id = f"req_{user.id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # 生成随机手机号
            number = f"1{random.randint(3, 9)}{random.randint(100000000, 999999999)}"
            
            # 创建号码记录
            phone_number = PhoneNumber(
                request_id=request_id,
                number=number,
                project_id=project.id,
                user_id=user.id,
                price=project.price,
                status=NumberStatus.ACTIVE,
                message_count=0
            )
            
            # 扣除用户余额
            user.balance -= project.price
            
            # 保存到数据库
            session.add(phone_number)
            session.commit()
            
            # 返回号码信息
            return jsonify({
                "number": {
                    "id": request_id,
                    "number": number,
                    "project_id": project.id,
                    "project_name": project.name,
                    "price": project.price,
                    "status": "active",
                    "created_at": phone_number.created_at.isoformat() if hasattr(phone_number.created_at, 'isoformat') else str(phone_number.created_at)
                }
            })
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"获取号码时发生数据库错误: {str(e)}")
            return jsonify({"error": f"获取号码失败: {str(e)}", "code": 500}), 500
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("获取号码时发生异常")
        return jsonify({"error": f"获取号码失败: {str(e)}", "code": 500}), 500

@number_bp.route('/<string:request_id>/status', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/numbers/{id}/status")
def get_number_status(request_id):
    """获取号码状态"""
    try:
        session = db.get_session()
        try:
            # 查询号码记录
            phone_number = session.query(PhoneNumber).filter_by(request_id=request_id).first()
            if not phone_number:
                return jsonify({"error": "号码记录不存在", "code": 404}), 404
            
            # 检查所有权
            user = g.current_user
            if phone_number.user_id != user.id and not user.is_admin:
                return jsonify({"error": "无权访问此号码", "code": 403}), 403
            
            # 获取项目信息
            project = session.query(Project).get(phone_number.project_id)
            
            # 返回状态信息
            return jsonify({
                "status": phone_number.status.value if phone_number.status else "unknown",
                "number": phone_number.number,
                "project_id": phone_number.project_id,
                "project_name": project.name if project else None,
                "message_count": phone_number.message_count,
                "created_at": phone_number.created_at.isoformat() if hasattr(phone_number.created_at, 'isoformat') else str(phone_number.created_at),
                "updated_at": phone_number.updated_at.isoformat() if hasattr(phone_number.updated_at, 'isoformat') else str(phone_number.updated_at)
            })
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception(f"获取号码状态时发生异常，请求ID: {request_id}")
        return jsonify({"error": f"获取号码状态失败: {str(e)}", "code": 500}), 500

@number_bp.route('/<string:request_id>/messages', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/numbers/{id}/messages")
def get_messages(request_id):
    """获取号码短信"""
    try:
        session = db.get_session()
        try:
            # 查询号码记录
            phone_number = session.query(PhoneNumber).filter_by(request_id=request_id).first()
            if not phone_number:
                return jsonify({"error": "号码记录不存在", "code": 404}), 404
            
            # 检查所有权
            user = g.current_user
            if phone_number.user_id != user.id and not user.is_admin:
                return jsonify({"error": "无权访问此号码", "code": 403}), 403
            
            # 获取所有短信
            messages = session.query(Message).filter_by(phone_number_id=phone_number.id).all()
            
            # 转换为字典列表
            message_list = [
                {
                    "id": message.id,
                    "sender": message.sender,
                    "content": message.content,
                    "code": message.code,
                    "received_at": message.created_at.isoformat() if hasattr(message.created_at, 'isoformat') else str(message.created_at)
                }
                for message in messages
            ]
            
            # 如果没有短信但号码状态为活跃，模拟生成一条短信
            if not message_list and phone_number.status == NumberStatus.ACTIVE:
                # 随机生成验证码
                code = "".join([str(random.randint(0, 9)) for _ in range(6)])
                
                # 随机生成发送者
                senders = ["10010", "10086", "10000", "95588", "106"]
                sender = random.choice(senders) + "".join([str(random.randint(0, 9)) for _ in range(5)])
                
                # 随机生成内容
                templates = [
                    f"您的验证码是{code}，5分钟内有效，请勿泄露给他人。",
                    f"您正在登录，验证码{code}，请勿泄露给他人。",
                    f"您的验证码为{code}，有效期10分钟，请勿告知他人。",
                    f"验证码{code}，用于身份验证，请勿转发他人。"
                ]
                content = random.choice(templates)
                
                # 创建消息记录
                now = time.strftime("%Y-%m-%d %H:%M:%S")
                message = Message(
                    phone_number_id=phone_number.id,
                    sender=sender,
                    content=content,
                    code=code
                )
                
                # 更新号码记录的消息计数
                phone_number.message_count += 1
                
                # 添加到数据库
                session.add(message)
                session.commit()
                
                # 添加到结果中
                message_list.append({
                    "id": message.id,
                    "sender": sender,
                    "content": content,
                    "code": code,
                    "received_at": message.created_at.isoformat() if hasattr(message.created_at, 'isoformat') else str(message.created_at)
                })
            
            return jsonify({
                "items": message_list,
                "total": len(message_list)
            })
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"获取短信时发生数据库错误: {str(e)}")
            return jsonify({"error": f"获取短信失败: {str(e)}", "code": 500}), 500
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception(f"获取短信时发生异常，请求ID: {request_id}")
        return jsonify({"error": f"获取短信失败: {str(e)}", "code": 500}), 500

@number_bp.route('/<string:request_id>/release', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/numbers/{id}/release")
def release_number(request_id):
    """释放号码"""
    try:
        session = db.get_session()
        try:
            # 查询号码记录
            phone_number = session.query(PhoneNumber).filter_by(request_id=request_id).first()
            if not phone_number:
                return jsonify({"error": "号码记录不存在", "code": 404}), 404
            
            # 检查所有权
            user = g.current_user
            if phone_number.user_id != user.id and not user.is_admin:
                return jsonify({"error": "无权访问此号码", "code": 403}), 403
            
            # 检查状态
            if phone_number.status == NumberStatus.RELEASED:
                return jsonify({"message": "号码已经释放"})
            
            # 更新状态
            phone_number.status = NumberStatus.RELEASED
            
            # 保存到数据库
            session.commit()
            
            return jsonify({
                "message": "号码已释放成功",
                "number": phone_number.number
            })
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"释放号码时发生数据库错误: {str(e)}")
            return jsonify({"error": f"释放号码失败: {str(e)}", "code": 500}), 500
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception(f"释放号码时发生异常，请求ID: {request_id}")
        return jsonify({"error": f"释放号码失败: {str(e)}", "code": 500}), 500

@number_bp.route('/history', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/numbers/history")
def get_history():
    """获取号码历史记录"""
    try:
        # 获取参数
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        # 限制每页数量
        if per_page > 100:
            per_page = 100
        
        session = db.get_session()
        try:
            # 查询用户的号码记录
            user = g.current_user
            query = session.query(PhoneNumber).filter_by(user_id=user.id)
            
            # 计算总数
            total = query.count()
            
            # 执行分页查询
            phone_numbers = query.order_by(PhoneNumber.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
            
            # 获取项目信息
            project_ids = [pn.project_id for pn in phone_numbers]
            projects = session.query(Project).filter(Project.id.in_(project_ids)).all()
            project_map = {p.id: p for p in projects}
            
            # 转换为字典列表
            history_list = [
                {
                    "id": pn.request_id,
                    "number": pn.number,
                    "project_id": pn.project_id,
                    "project_name": project_map.get(pn.project_id).name if pn.project_id in project_map else None,
                    "price": pn.price,
                    "status": pn.status.value if pn.status else "unknown",
                    "message_count": pn.message_count,
                    "created_at": pn.created_at.isoformat() if hasattr(pn.created_at, 'isoformat') else str(pn.created_at)
                }
                for pn in phone_numbers
            ]
            
            return jsonify({
                "items": history_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            })
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("获取号码历史记录时发生异常")
        return jsonify({"error": f"获取号码历史记录失败: {str(e)}", "code": 500}), 500 