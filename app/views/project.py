#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, g
from app.middlewares.auth_middleware import auth_required
from app.services.monitoring import monitor_api
from app.database import db
from app.models.project import Project
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
project_bp = Blueprint('project', __name__)

@project_bp.route('', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/projects")
def get_projects():
    """获取项目列表"""
    try:
        # 获取参数
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        # 限制每页数量
        if per_page > 100:
            per_page = 100
        
        # 查询项目
        session = db.get_session()
        try:
            query = session.query(Project).filter(Project.available == True)
            
            # 计算总数
            total = query.count()
            
            # 执行分页查询
            projects = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # 转换为字典列表
            project_list = [project.to_dict() for project in projects]
            
            return jsonify({
                "items": project_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            })
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("获取项目列表时发生异常")
        return jsonify({"error": f"获取项目列表失败: {str(e)}", "code": 500}), 500

@project_bp.route('/<int:project_id>', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/projects/{id}")
def get_project(project_id):
    """获取项目详情"""
    try:
        session = db.get_session()
        try:
            # 查询项目
            project = session.query(Project).get(project_id)
            
            if not project:
                return jsonify({"error": "项目不存在", "code": 404}), 404
            
            # 检查项目可用性
            if not project.available:
                return jsonify({"error": "项目不可用", "code": 403}), 403
            
            return jsonify({
                "project": project.to_dict()
            })
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception(f"获取项目详情时发生异常，项目ID: {project_id}")
        return jsonify({"error": f"获取项目详情失败: {str(e)}", "code": 500}), 500

@project_bp.route('/search', methods=['GET'])
@auth_required
@monitor_api(endpoint="/api/projects/search")
def search_projects():
    """搜索项目"""
    try:
        # 获取参数
        keyword = request.args.get('keyword', '')
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        # 限制每页数量
        if per_page > 100:
            per_page = 100
        
        session = db.get_session()
        try:
            # 构建查询
            query = session.query(Project).filter(Project.available == True)
            
            # 添加关键词过滤
            if keyword:
                query = query.filter(
                    (Project.name.ilike(f'%{keyword}%')) |
                    (Project.description.ilike(f'%{keyword}%')) |
                    (Project.code.ilike(f'%{keyword}%'))
                )
            
            # 计算总数
            total = query.count()
            
            # 执行分页查询
            projects = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # 转换为字典列表
            project_list = [project.to_dict() for project in projects]
            
            return jsonify({
                "items": project_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
                "keyword": keyword
            })
        
        finally:
            db.close_session()
    
    except Exception as e:
        logger.exception("搜索项目时发生异常")
        return jsonify({"error": f"搜索项目失败: {str(e)}", "code": 500}), 500 