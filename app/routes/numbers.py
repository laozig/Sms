from flask import Blueprint, request, jsonify, current_app, send_file
from datetime import datetime, timedelta
from app.models import db, PhoneNumber, Project, User, BlacklistedNumber, Transaction, PhoneRequest, SMS
from app.utils import token_required, admin_required, SMSApiClient, calculate_price, validate_pagination_params
from sqlalchemy import desc, func
import uuid
import random
import string
import os
import csv
import json
import io
import pandas as pd
import re

# 定义验证码提取函数
def extract_verification_code(content):
    """
    从短信内容中提取验证码
    
    参数:
        content: 短信内容
        
    返回:
        提取出的验证码，如果未找到则返回空字符串
    """
    # 常见的验证码模式
    patterns = [
        r'验证码[是为:]?\s*([0-9]{4,6})',  # 验证码是123456
        r'code[: ]([0-9]{4,6})',  # code: 123456
        r'码[是为:]?\s*([0-9]{4,6})',  # 码是123456
        r'[验证认证校验].*?([0-9]{4,6})',  # 您的验证码123456
        r'([0-9]{4,6})[^0-9]*验证',  # 123456是您的验证码
        r'([0-9]{6})',  # 直接匹配6位数字
        r'([0-9]{4})'   # 直接匹配4位数字
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    
    return ""

# 创建蓝图
numbers_bp = Blueprint('numbers', __name__)


@numbers_bp.route('/get', methods=['GET', 'POST'])
@token_required
def get_phone_number():
    """
    取号（获取手机号）
    
    请求参数:
        project_code: 项目代码
    
    返回:
        成功: {'message': '获取号码成功', 'phone_number': 号码信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取项目代码
    project_code = args.get('project_code')
    if not project_code:
        return jsonify({
            'message': '请提供项目代码', 
            'help': '示例请求: /api/numbers/get?token=您的令牌&project_code=项目代码'
        }), 400
    
    # 查询项目
    project = Project.query.filter_by(code=project_code).first()
    if not project:
        return jsonify({'message': f'项目代码 {project_code} 不存在'}), 404
    
    # 查询用户
    user = User.query.get(request.user_id)
    
    # 检查余额
    if user.balance < project.price:
        return jsonify({'message': f'余额不足，当前余额: {user.balance}，需要: {project.price}'}), 400
    
    # 生成请求ID
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    
    # 尝试连接SMS API获取手机号
    try:
        api_client = SMSApiClient()
        api_result = api_client.get_phone_number(project_code)
        
        # 如果使用模拟API或者成功获取号码
        if api_client.use_mock or api_result.get('success', False):
            # 从API结果中获取号码，如果未找到则生成模拟号码
            phone_data = api_result.get('phone_number', {})
            phone_number = phone_data.get('number') if phone_data else f"138{random.randint(10000000, 99999999)}"
            
            # 先创建空对象
            new_phone = PhoneNumber()
            # 然后设置属性
            new_phone.number = phone_number
            new_phone.status = 'available'
            new_phone.project_id = project.id
            new_phone.user_id = user.id
            new_phone.request_id = request_id
            new_phone.created_at = datetime.utcnow()
            new_phone.updated_at = datetime.utcnow()
            
            db.session.add(new_phone)
            
            # 创建消费记录
            transaction = Transaction(
                user_id=user.id,
                amount=-project.price,
                balance=user.balance - project.price,
                type='consume',
                description=f'获取项目{project.name}的手机号码',
                reference_id=request_id
            )
            
            db.session.add(transaction)
            
            # 扣除余额
            user.balance -= project.price
            
            db.session.commit()
            
            # 查询添加的记录并返回
            phone = PhoneNumber.query.filter_by(request_id=request_id).first()
            
            return jsonify({
                'message': '获取号码成功',
                'phone_number': phone.to_dict(),
                'get_sms_url': f"{request.url_root}api/numbers/sms/{request_id}?token={args.get('token', '')}"
            }), 200
        else:
            return jsonify({'message': f'无法获取手机号: {api_result.get("message", "未知错误")}'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'处理号码失败: {str(e)}'}), 500


@numbers_bp.route('/get-specific', methods=['GET', 'POST'])
@token_required
def get_specific_phone_number():
    """
    指定取号（获取指定手机号）
    
    请求参数:
        project_code: 项目代码
        number: 手机号码
    
    返回:
        成功: {'message': '获取号码成功', 'phone_number': 号码信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取参数
    project_code = args.get('project_code')
    number = args.get('number')
    
    if not project_code or not number:
        return jsonify({
            'message': '请提供项目代码和手机号码',
            'help': '示例请求: /api/numbers/get-specific?token=您的令牌&project_code=项目代码&number=13800138000'
        }), 400
    
    # 查询项目
    project = Project.query.filter_by(code=project_code).first()
    if not project:
        return jsonify({'message': f'项目代码 {project_code} 不存在'}), 404
    
    # 查询用户
    user = User.query.get(request.user_id)
    
    # 检查余额
    if user.balance < project.price:
        return jsonify({'message': f'余额不足，当前余额: {user.balance}，需要: {project.price}'}), 400
    
    # 检查号码是否在黑名单中
    if BlacklistedNumber.query.filter_by(number=number).first():
        return jsonify({'message': f'号码 {number} 已被拉黑'}), 400
    
    # 检查号码是否已被他人使用
    if PhoneNumber.query.filter_by(number=number, status='available').first():
        return jsonify({'message': f'号码 {number} 已被使用'}), 400
    
    # 生成请求ID
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    
    # 尝试通过SMS API获取指定号码
    try:
        api_client = SMSApiClient()
        api_result = api_client.get_specific_phone_number(project_code, number)
        
        # 如果使用模拟API或者成功获取号码
        if api_client.use_mock or api_result.get('success', False):
            # 先创建空对象
            new_phone = PhoneNumber()
            # 然后设置属性
            new_phone.number = number
            new_phone.status = 'available'
            new_phone.project_id = project.id
            new_phone.user_id = user.id
            new_phone.request_id = request_id
            new_phone.created_at = datetime.utcnow()
            new_phone.updated_at = datetime.utcnow()
            
            db.session.add(new_phone)
            
            # 创建消费记录
            transaction = Transaction(
                user_id=user.id,
                amount=-project.price,
                balance=user.balance - project.price,
                type='consume',
                description=f'获取项目{project.name}的指定手机号码',
                reference_id=request_id
            )
            
            db.session.add(transaction)
            
            # 扣除余额
            user.balance -= project.price
            
            db.session.commit()
            
            # 查询添加的记录并返回
            phone = PhoneNumber.query.filter_by(request_id=request_id).first()
            
            return jsonify({
                'message': '获取号码成功',
                'phone_number': phone.to_dict(),
                'get_sms_url': f"{request.url_root}api/numbers/sms/{request_id}?token={args.get('token', '')}"
            }), 200
        else:
            return jsonify({'message': f'无法获取指定号码: {api_result.get("message", "未知错误")}'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'处理号码失败: {str(e)}'}), 500


@numbers_bp.route('/sms/<request_id>', methods=['GET', 'POST'])
@token_required
def get_sms_code(request_id):
    """
    获取短信验证码
    
    请求参数:
        request_id: 请求ID
    
    返回:
        成功: {'message': '获取验证码成功', 'code': 验证码, 'phone_number': 号码信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 查询号码
    phone = PhoneNumber.query.filter_by(
        request_id=request_id, 
        user_id=request.user_id
    ).first()
    
    if not phone:
        return jsonify({
            'message': '未找到该请求ID的号码',
            'help': f'请检查请求ID {request_id} 是否正确, 并确认是您的号码'
        }), 404
    
    if phone.status != 'available' and phone.status != 'used':
        return jsonify({'message': f'号码状态为 {phone.status}，无法获取验证码。只有available或used状态的号码可以获取验证码'}), 400
    
    # 如果已有验证码，直接返回
    if phone.sms_code:
        return jsonify({
            'message': '获取验证码成功',
            'code': phone.sms_code,
            'phone_number': phone.to_dict()
        }), 200
    
    # 尝试通过SMS API获取验证码
    try:
        api_client = SMSApiClient()
        api_result = api_client.get_sms_code(request_id)
        
        # 如果使用模拟API或者成功获取验证码
        if api_client.use_mock or api_result.get('success', False):
            # 从API结果中获取验证码，如果未找到则生成随机验证码
            sms_code = api_result.get('code') if api_result.get('code') else ''.join(random.choices(string.digits, k=6))
            
            # 更新号码状态和验证码
            phone.status = 'used'
            phone.sms_code = sms_code
            phone.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'message': '获取验证码成功',
                'code': sms_code,
                'phone_number': phone.to_dict(),
                'release_url': f"{request.url_root}api/numbers/release/{request_id}?token={request.args.get('token', '')}"
            }), 200
        else:
            return jsonify({'message': f'无法获取验证码: {api_result.get("message", "未知错误")}'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'获取验证码失败: {str(e)}'}), 500


@numbers_bp.route('/release/<request_id>', methods=['GET', 'POST'])
@token_required
def release_phone_number(request_id):
    """
    释放号码
    
    请求参数:
        request_id: 请求ID
    
    返回:
        成功: {'message': '号码释放成功'}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 查询号码
    phone = PhoneNumber.query.filter_by(
        request_id=request_id, 
        user_id=request.user_id
    ).first()
    
    if not phone:
        return jsonify({
            'message': '未找到该请求ID的号码',
            'help': f'请检查请求ID {request_id} 是否正确, 并确认是您的号码'
        }), 404
    
    if phone.status == 'released':
        return jsonify({'message': '号码已释放', 'phone_number': phone.to_dict()}), 200
    
    # 尝试通过SMS API释放号码
    try:
        api_client = SMSApiClient()
        api_result = api_client.release_phone_number(request_id)
        
        # 如果使用模拟API或者成功释放号码
        if api_client.use_mock or api_result.get('success', False):
            # 更新号码状态
            phone.status = 'released'
            phone.released_at = datetime.utcnow()
            phone.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'message': '号码释放成功',
                'phone_number': phone.to_dict()
            }), 200
        else:
            return jsonify({'message': f'无法释放号码: {api_result.get("message", "未知错误")}'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'释放号码失败: {str(e)}'}), 500


@numbers_bp.route('/blacklist', methods=['GET', 'POST'])
@token_required
def blacklist_number():
    """
    拉黑号码
    
    请求参数:
        number: 手机号码
        reason: 拉黑原因（可选）
    
    返回:
        成功: {'message': '号码已加入黑名单'}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取参数
    number = args.get('number')
    reason = args.get('reason')
    
    if not number:
        return jsonify({
            'message': '请提供手机号码',
            'help': '示例请求: /api/numbers/blacklist?token=您的令牌&number=13800138000&reason=原因'
        }), 400
    
    # 检查号码是否已在黑名单中
    existing = BlacklistedNumber.query.filter_by(number=number).first()
    if existing:
        # 返回200而不是400，并显示成功消息
        return jsonify({'message': f'号码 {number} 已在黑名单中', 'blacklisted_number': existing.to_dict()}), 200
    
    # 尝试通过SMS API拉黑号码
    try:
        api_client = SMSApiClient()
        api_result = api_client.blacklist_phone_number(number, reason)
        
        # 如果使用模拟API或者成功拉黑号码
        if api_client.use_mock or api_result.get('success', False):
            # 创建黑名单记录
            blacklisted = BlacklistedNumber(
                number=number,
                reason=reason,
                created_at=datetime.utcnow()
            )
            
            db.session.add(blacklisted)
            
            # 更新相关的号码记录状态
            phones = PhoneNumber.query.filter_by(number=number).all()
            for phone in phones:
                phone.status = 'blacklisted'
                phone.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'message': '号码已加入黑名单',
                'blacklisted_number': blacklisted.to_dict()
            }), 200
        else:
            return jsonify({'message': f'无法拉黑号码: {api_result.get("message", "未知错误")}'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'拉黑号码失败: {str(e)}'}), 500


@numbers_bp.route('/my-numbers', methods=['GET', 'POST'])
@token_required
def get_my_numbers():
    """
    获取我的号码列表
    
    请求参数:
        page: 页码（默认1）
        per_page: 每页数量（默认10）
        status: 状态过滤（可选：available, used, released, blacklisted）
    
    返回:
        成功: 号码列表分页数据
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取分页参数
    page = args.get('page')
    per_page = args.get('per_page')
    page, per_page = validate_pagination_params(page, per_page)
    
    # 状态过滤
    status = args.get('status')
    
    # 查询条件
    query = PhoneNumber.query.filter_by(user_id=request.user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    # 排序（最新的在前）
    query = query.order_by(desc(PhoneNumber.created_at))
    
    try:
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        
        # 构建结果，包含分页信息和项目列表
        result = {
            'items': [item.to_dict() for item in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
        
        # 添加帮助信息
        result['help'] = {
            'example_get_number': f"{request.url_root}api/numbers/get?token={args.get('token', '')}&project_code=项目代码",
            'example_get_specific': f"{request.url_root}api/numbers/get-specific?token={args.get('token', '')}&project_code=项目代码&number=13800138000",
            'example_get_sms': f"{request.url_root}api/numbers/sms/请求ID?token={args.get('token', '')}"
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'message': f'查询号码列表失败: {str(e)}'}), 500


@numbers_bp.route('/batch-get', methods=['GET', 'POST'])
@token_required
def batch_get_numbers():
    """
    批量取号（批量获取手机号）
    
    请求参数:
        project_code: 项目代码
        count: 需要获取的号码数量(1-10)
    
    返回:
        成功: {'message': '批量获取号码成功', 'phone_numbers': 号码列表}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取项目代码和数量
    project_code = args.get('project_code')
    count = args.get('count', 1)
    
    # 验证参数
    if not project_code:
        return jsonify({
            'message': '请提供项目代码', 
            'help': '示例请求: /api/numbers/batch-get?token=您的令牌&project_code=项目代码&count=3'
        }), 400
    
    try:
        count = int(count)
        if count < 1 or count > 10:
            return jsonify({'message': '数量必须在1-10之间'}), 400
    except ValueError:
        return jsonify({'message': '数量必须是整数'}), 400
    
    # 查询项目
    project = Project.query.filter_by(code=project_code).first()
    if not project:
        return jsonify({'message': f'项目代码 {project_code} 不存在'}), 404
    
    # 查询用户
    user = User.query.get(request.user_id)
    
    # 计算总价
    total_price = project.price * count
    
    # 检查余额
    if user.balance < total_price:
        return jsonify({'message': f'余额不足，当前余额: {user.balance}，需要: {total_price}'}), 400
    
    # 批量获取号码
    phone_numbers = []
    request_ids = []
    
    try:
        api_client = SMSApiClient()
        
        for _ in range(count):
            # 生成请求ID
            request_id = f"req_{uuid.uuid4().hex[:8]}"
            request_ids.append(request_id)
            
            # 获取手机号
            api_result = api_client.get_phone_number(project_code)
            
            # 如果使用模拟API或者成功获取号码
            if api_client.use_mock or api_result.get('success', False):
                # 从API结果中获取号码，如果未找到则生成模拟号码
                phone_data = api_result.get('phone_number', {})
                phone_number = phone_data.get('number') if phone_data else f"138{random.randint(10000000, 99999999)}"
                
                # 创建手机号记录
                new_phone = PhoneNumber()
                new_phone.number = phone_number
                new_phone.status = 'available'
                new_phone.project_id = project.id
                new_phone.user_id = user.id
                new_phone.request_id = request_id
                new_phone.created_at = datetime.utcnow()
                new_phone.updated_at = datetime.utcnow()
                
                db.session.add(new_phone)
                
                # 保存到结果列表
                phone_numbers.append(new_phone)
            else:
                # 回滚已添加的记录
                db.session.rollback()
                return jsonify({'message': f'获取第 {len(phone_numbers)+1} 个号码失败: {api_result.get("message", "未知错误")}'}), 400
        
        # 创建消费记录
        transaction = Transaction(
            user_id=user.id,
            amount=-total_price,
            balance=user.balance - total_price,
            type='consume',
            description=f'批量获取{count}个项目{project.name}的手机号码',
            reference_id=','.join(request_ids)
        )
        
        db.session.add(transaction)
        
        # 扣除余额
        user.balance -= total_price
        
        db.session.commit()
        
        # 构建响应数据
        response_data = []
        for phone in phone_numbers:
            phone_dict = phone.to_dict()
            phone_dict['get_sms_url'] = f"{request.url_root}api/numbers/sms/{phone.request_id}?token={args.get('token', '')}"
            response_data.append(phone_dict)
        
        # 构建批量操作链接
        batch_release_url = f"{request.url_root}api/numbers/batch-release?token={args.get('token', '')}&request_ids={','.join(request_ids)}"
        
        return jsonify({
            'message': '批量获取号码成功',
            'phone_numbers': response_data,
            'count': len(phone_numbers),
            'batch_release_url': batch_release_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'批量获取号码失败: {str(e)}'}), 500


@numbers_bp.route('/batch-release', methods=['GET', 'POST'])
@token_required
def batch_release_numbers():
    """
    批量释放号码
    
    请求参数:
        request_ids: 请求ID列表，用逗号分隔
    
    返回:
        成功: {'message': '批量释放号码成功', 'released': 释放成功的数量}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取请求ID列表
    request_ids_str = args.get('request_ids')
    if not request_ids_str:
        return jsonify({
            'message': '请提供请求ID列表',
            'help': '示例请求: /api/numbers/batch-release?token=您的令牌&request_ids=req_12345abc,req_67890def'
        }), 400
    
    # 分割ID列表
    request_ids = [id.strip() for id in request_ids_str.split(',') if id.strip()]
    if not request_ids:
        return jsonify({'message': '无效的请求ID列表'}), 400
    
    # 查询用户
    user_id = request.user_id
    
    # 查询要释放的号码
    phones_to_release = PhoneNumber.query.filter(
        PhoneNumber.request_id.in_(request_ids),
        PhoneNumber.user_id == user_id,
        PhoneNumber.status.in_(['available', 'used'])
    ).all()
    
    if not phones_to_release:
        return jsonify({'message': '未找到可释放的号码'}), 404
    
    # 初始化API客户端
    api_client = SMSApiClient()
    
    # 记录释放结果
    release_results = {
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    # 批量释放号码
    for phone in phones_to_release:
        try:
            # 调用API释放号码
            if api_client.use_mock or api_client.release_phone_number(phone.request_id).get('success', False):
                # 更新号码状态
                phone.status = 'released'
                phone.released_at = datetime.utcnow()
                phone.updated_at = datetime.utcnow()
                
                release_results['success'] += 1
                release_results['details'].append({
                    'request_id': phone.request_id,
                    'number': phone.number,
                    'status': 'success'
                })
            else:
                release_results['failed'] += 1
                release_results['details'].append({
                    'request_id': phone.request_id,
                    'number': phone.number,
                    'status': 'failed',
                    'reason': '调用API释放失败'
                })
        except Exception as e:
            release_results['failed'] += 1
            release_results['details'].append({
                'request_id': phone.request_id,
                'number': phone.number,
                'status': 'failed',
                'reason': str(e)
            })
    
    # 提交数据库事务
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'批量释放号码失败: {str(e)}'}), 500
    
    return jsonify({
        'message': f'批量释放号码完成: {release_results["success"]}个成功, {release_results["failed"]}个失败',
        'released': release_results['success'],
        'failed': release_results['failed'],
        'details': release_results['details']
    }), 200


@numbers_bp.route('/export', methods=['GET', 'POST'])
@token_required
def export_numbers():
    """
    导出号码记录
    
    请求参数:
        format: 导出格式(csv, json, excel)
        start_date: 开始日期(YYYY-MM-DD)
        end_date: 结束日期(YYYY-MM-DD)
        status: 状态过滤（可选）
    
    返回:
        成功: {'message': '导出成功', 'download_url': 下载链接}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取参数
    export_format = args.get('format', 'csv').lower()
    start_date_str = args.get('start_date')
    end_date_str = args.get('end_date')
    status = args.get('status')
    
    # 验证格式
    if export_format not in ['csv', 'json', 'excel']:
        return jsonify({
            'message': '无效的导出格式',
            'help': '有效的格式: csv, json, excel'
        }), 400
    
    try:
        # 处理日期
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # 设置到当天结束
            end_date = end_date.replace(hour=23, minute=59, second=59)
        else:
            end_date = datetime.now()
    except ValueError:
        return jsonify({'message': '无效的日期格式，请使用YYYY-MM-DD格式'}), 400
    
    # 查询用户号码
    query = PhoneNumber.query.filter(
        PhoneNumber.user_id == request.user_id,
        PhoneNumber.created_at.between(start_date, end_date)
    )
    
    # 应用状态过滤
    if status:
        query = query.filter(PhoneNumber.status == status)
    
    # 获取数据
    phones = query.order_by(desc(PhoneNumber.created_at)).all()
    
    if not phones:
        return jsonify({'message': '未找到符合条件的记录'}), 404
    
    # 准备导出数据
    export_data = []
    for phone in phones:
        # 获取关联的项目信息
        project = Project.query.get(phone.project_id)
        project_name = project.name if project else "未知项目"
        project_code = project.code if project else "未知代码"
        
        # 构建记录
        record = {
            'id': phone.id,
            'number': phone.number,
            'status': phone.status,
            'project_name': project_name,
            'project_code': project_code,
            'request_id': phone.request_id,
            'created_at': phone.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': phone.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'sms_code': phone.sms_code or '',
            'released_at': phone.released_at.strftime('%Y-%m-%d %H:%M:%S') if phone.released_at else ''
        }
        export_data.append(record)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename_base = f"numbers_export_{timestamp}"
    
    # 生成响应
    if export_format == 'csv':
        # 创建内存文件
        output = io.StringIO()
        # 获取字段名（从第一条记录）
        fieldnames = export_data[0].keys() if export_data else []
        # 创建CSV写入器
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        # 写入表头
        writer.writeheader()
        # 写入数据
        writer.writerows(export_data)
        
        # 准备响应
        output.seek(0)
        filename = f"{filename_base}.csv"
        
        return jsonify({
            'message': '导出CSV成功',
            'record_count': len(export_data),
            'data': output.getvalue()
        }), 200
        
    elif export_format == 'json':
        # 直接返回JSON数据
        return jsonify({
            'message': '导出JSON成功',
            'record_count': len(export_data),
            'data': export_data
        }), 200
        
    else:  # excel
        try:
            # 创建DataFrame
            df = pd.DataFrame(export_data)
            # 创建内存文件
            output = io.BytesIO()
            # 写入Excel
            df.to_excel(output, index=False)
            # 准备响应
            output.seek(0)
            
            # 转换为Base64字符串
            import base64
            excel_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
            
            return jsonify({
                'message': '导出Excel成功',
                'record_count': len(export_data),
                'data': excel_base64
            }), 200
        except Exception as e:
            return jsonify({'message': f'导出Excel失败: {str(e)}'}), 500


@numbers_bp.route('/batch-sms', methods=['GET', 'POST'])
@token_required
def batch_get_sms():
    """
    批量获取短信
    
    参数:
        token: 认证令牌
        request_ids: 请求ID列表，用逗号分隔
    
    返回:
        多个请求ID对应的短信信息
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    # 获取请求参数
    request_ids_str = request.args.get('request_ids', '') or request.form.get('request_ids', '')
    
    if not request_ids_str:
        return jsonify({
            'status': 'error',
            'message': '请提供请求ID列表'
        }), 400
    
    # 解析请求ID列表
    request_ids = [req_id.strip() for req_id in request_ids_str.split(',') if req_id.strip()]
    
    if not request_ids:
        return jsonify({
            'status': 'error',
            'message': '无效的请求ID列表'
        }), 400
    
    # 限制批量查询数量
    if len(request_ids) > 10:
        return jsonify({
            'status': 'error',
            'message': '一次最多查询10个请求ID的短信'
        }), 400
    
    # 查询所有请求ID对应的短信
    results = {}
    for request_id in request_ids:
        # 查询号码请求
        phone_request = PhoneRequest.query.filter_by(request_id=request_id).first()
        
        if not phone_request:
            results[request_id] = {
                'status': 'error',
                'message': '请求ID不存在'
            }
            continue
        
        # 检查权限（只能查询自己的号码）
        if phone_request.user_id != current_user_id:
            results[request_id] = {
                'status': 'error',
                'message': '无权查询此请求ID'
            }
            continue
        
        # 检查号码状态
        if phone_request.status not in ['active', 'used']:
            results[request_id] = {
                'status': 'error',
                'message': f'号码状态不正确: {phone_request.status}'
            }
            continue
        
        # 查询短信
        sms = SMS.query.filter_by(phone_request_id=phone_request.id).order_by(SMS.received_at.desc()).first()
        
        if not sms:
            results[request_id] = {
                'status': 'waiting',
                'message': '暂无短信，请稍后再试'
            }
            continue
        
        # 返回短信信息
        results[request_id] = {
            'status': 'success',
            'phone_number': phone_request.phone_number,
            'sms': {
                'id': sms.id,
                'sender': sms.sender,
                'content': sms.content,
                'received_at': sms.received_at.isoformat(),
                'code': extract_verification_code(sms.content)
            }
        }
    
    return jsonify({
        'status': 'success',
        'results': results
    }) 