#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, g
from app.middlewares.auth_middleware import admin_required
from app.services.monitoring import monitor_api
from app.database import db
from app.models.user import User
from app.models.project import Project
from app.models.number import PhoneNumber, NumberStatus
from app.services.async_service import task_manager
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# 创建蓝图
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@admin_required
@monitor_api(endpoint="/api/admin/users")
def get_users():
    """获取用户列表"""
    try:
        # 获取参数
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        filter_str = request.args.get('filter', '')
        
        # 限制每页数量
        if per_page > 100:
            per_page = 100
        
        session = db.get_session()
        try:
            # 构建查询
            query = session.query(User)
            
            # 添加过滤条件
            if filter_str:
                query = query.filter(
                    (User.username.ilike(f'%{filter_str}%')) |
                    (User.email.ilike(f'%{filter_str}%'))
                )
            
            # 计算总数
            total = query.count()
            
            # 执行分页查询
            users = query.order_by(User.id).offset((page - 1) * per_page).limit(per_page).all()
            
            # 转换为字典列表
            user_list = [user.to_dict() for user in users]
            
            return jsonify({
                "items": user_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
                "filter": filter_str
            })
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("获取用户列表时发生异常")
        return jsonify({"error": f"获取用户列表失败: {str(e)}", "code": 500}), 500

@admin_bp.route('/users/<int:user_id>/update', methods=['POST'])
@admin_required
@monitor_api(endpoint="/api/admin/users/{id}/update")
def update_user(user_id):
    """更新用户信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误", "code": 400}), 400
        
        session = db.get_session()
        try:
            # 查询用户
            user = session.query(User).get(user_id)
            if not user:
                return jsonify({"error": "用户不存在", "code": 404}), 404
            
            # 更新可编辑字段
            if 'is_active' in data:
                user.is_active = bool(data['is_active'])
            
            if 'is_admin' in data:
                user.is_admin = bool(data['is_admin'])
            
            if 'balance' in data:
                try:
                    balance = float(data['balance'])
                    user.balance = balance
                except (ValueError, TypeError):
                    return jsonify({"error": "余额必须为数字", "code": 400}), 400
            
            if 'email' in data:
                # 检查邮箱是否已被其他用户使用
                existing_email = session.query(User).filter(
                    User.email == data['email'],
                    User.id != user_id
                ).first()
                
                if existing_email:
                    return jsonify({"error": "邮箱已被其他用户使用", "code": 400}), 400
                
                user.email = data['email']
            
            # 提交更改
            session.commit()
            
            return jsonify({
                "message": "用户信息已更新",
                "user": user.to_dict()
            })
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"更新用户信息时发生数据库错误: {str(e)}")
            return jsonify({"error": f"数据库错误: {str(e)}", "code": 500}), 500
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception(f"更新用户信息时发生异常，用户ID: {user_id}")
        return jsonify({"error": f"更新用户信息失败: {str(e)}", "code": 500}), 500

@admin_bp.route('/projects', methods=['GET'])
@admin_required
@monitor_api(endpoint="/api/admin/projects")
def get_admin_projects():
    """获取项目列表 (管理员视图)"""
    try:
        # 获取参数
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        filter_str = request.args.get('filter', '')
        
        # 限制每页数量
        if per_page > 100:
            per_page = 100
        
        session = db.get_session()
        try:
            # 构建查询
            query = session.query(Project)
            
            # 添加过滤条件
            if filter_str:
                query = query.filter(
                    (Project.name.ilike(f'%{filter_str}%')) |
                    (Project.code.ilike(f'%{filter_str}%')) |
                    (Project.description.ilike(f'%{filter_str}%'))
                )
            
            # 计算总数
            total = query.count()
            
            # 执行分页查询
            projects = query.order_by(Project.id).offset((page - 1) * per_page).limit(per_page).all()
            
            # 转换为字典列表
            project_list = [project.to_dict() for project in projects]
            
            return jsonify({
                "items": project_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
                "filter": filter_str
            })
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("获取项目列表(管理员)时发生异常")
        return jsonify({"error": f"获取项目列表失败: {str(e)}", "code": 500}), 500

@admin_bp.route('/projects', methods=['POST'])
@admin_required
@monitor_api(endpoint="/api/admin/projects")
def create_project():
    """创建新项目"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误", "code": 400}), 400
        
        # 验证必填字段
        required_fields = ['name', 'code', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必填字段: {field}", "code": 400}), 400
        
        session = db.get_session()
        try:
            # 检查项目代码是否已存在
            existing_project = session.query(Project).filter_by(code=data['code']).first()
            if existing_project:
                return jsonify({"error": "项目代码已存在", "code": 400}), 400
            
            # 创建新项目
            project = Project(
                name=data['name'],
                code=data['code'],
                description=data.get('description', ''),
                price=float(data['price']),
                success_rate=float(data.get('success_rate', 0.9)),
                available=bool(data.get('available', True)),
                is_exclusive=bool(data.get('is_exclusive', False)),
                exclusive_id=data.get('exclusive_id')
            )
            
            # 保存到数据库
            session.add(project)
            session.commit()
            
            return jsonify({
                "message": "项目创建成功",
                "project": project.to_dict()
            })
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"创建项目时发生数据库错误: {str(e)}")
            return jsonify({"error": f"数据库错误: {str(e)}", "code": 500}), 500
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("创建项目时发生异常")
        return jsonify({"error": f"创建项目失败: {str(e)}", "code": 500}), 500

@admin_bp.route('/projects/<int:project_id>', methods=['PUT'])
@admin_required
@monitor_api(endpoint="/api/admin/projects/{id}")
def update_project(project_id):
    """更新项目信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误", "code": 400}), 400
        
        session = db.get_session()
        try:
            # 查询项目
            project = session.query(Project).get(project_id)
            if not project:
                return jsonify({"error": "项目不存在", "code": 404}), 404
            
            # 更新可编辑字段
            if 'name' in data:
                project.name = data['name']
            
            if 'description' in data:
                project.description = data['description']
            
            if 'price' in data:
                try:
                    project.price = float(data['price'])
                except (ValueError, TypeError):
                    return jsonify({"error": "价格必须为数字", "code": 400}), 400
            
            if 'success_rate' in data:
                try:
                    project.success_rate = float(data['success_rate'])
                except (ValueError, TypeError):
                    return jsonify({"error": "成功率必须为数字", "code": 400}), 400
            
            if 'available' in data:
                project.available = bool(data['available'])
            
            if 'is_exclusive' in data:
                project.is_exclusive = bool(data['is_exclusive'])
            
            if 'exclusive_id' in data:
                project.exclusive_id = data['exclusive_id']
            
            # 提交更改
            session.commit()
            
            return jsonify({
                "message": "项目信息已更新",
                "project": project.to_dict()
            })
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"更新项目信息时发生数据库错误: {str(e)}")
            return jsonify({"error": f"数据库错误: {str(e)}", "code": 500}), 500
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception(f"更新项目信息时发生异常，项目ID: {project_id}")
        return jsonify({"error": f"更新项目信息失败: {str(e)}", "code": 500}), 500

@admin_bp.route('/statistics', methods=['GET'])
@admin_required
@monitor_api(endpoint="/api/admin/statistics")
def get_admin_statistics():
    """获取管理员统计信息"""
    try:
        session = db.get_session()
        try:
            # 统计用户数量
            user_count = session.query(User).count()
            admin_count = session.query(User).filter_by(is_active=True, is_admin=True).count()
            normal_user_count = session.query(User).filter_by(is_active=True, is_admin=False).count()
            
            # 统计项目数量
            project_count = session.query(Project).count()
            active_project_count = session.query(Project).filter_by(available=True).count()
            
            # 统计号码数量
            number_count = session.query(PhoneNumber).count()
            active_number_count = session.query(PhoneNumber).filter_by(status=NumberStatus.ACTIVE).count()
            
            # 返回统计信息
            statistics = {
                "users": {
                    "total": user_count,
                    "admin": admin_count,
                    "normal": normal_user_count
                },
                "projects": {
                    "total": project_count,
                    "active": active_project_count
                },
                "numbers": {
                    "total": number_count,
                    "active": active_number_count
                }
            }
            
            return jsonify(statistics)
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("获取管理员统计信息时发生异常")
        return jsonify({"error": f"获取统计信息失败: {str(e)}", "code": 500}), 500 