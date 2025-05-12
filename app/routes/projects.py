from flask import Blueprint, request, jsonify, current_app
from app.models import db, Project, User, UserFavorite, UserExclusiveProject, PhoneNumber
from app.utils import token_required, admin_required, SMSApiClient, validate_pagination_params
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError

# 创建蓝图
projects_bp = Blueprint('projects', __name__)


@projects_bp.route('', methods=['GET', 'POST'])
@token_required
def get_projects():
    """
    获取项目列表
    
    请求参数:
        page: 页码（默认1）
        per_page: 每页数量（默认10）
        keyword: 搜索关键词（可选）
    
    返回:
        成功: 项目列表分页数据
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
    
    # 查询条件
    query = Project.query.filter_by(available=True)
    
    # 关键词搜索
    keyword = args.get('keyword')
    if keyword:
        query = query.filter(
            Project.name.ilike(f'%{keyword}%') | 
            Project.description.ilike(f'%{keyword}%')
        )
    
    # 执行分页查询
    try:
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'items': [item.to_dict() for item in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({'message': f'查询项目列表失败: {str(e)}'}), 500


@projects_bp.route('/search', methods=['GET', 'POST'])
@token_required
def search_projects():
    """
    搜索项目
    
    请求参数:
        keyword: 搜索关键词
    
    返回:
        成功: 项目列表
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取关键词
    keyword = args.get('keyword')
    if not keyword:
        return jsonify({'message': '请提供搜索关键词'}), 400
    
    # 执行查询
    try:
        projects = Project.query.filter(
            Project.available == True,
            (Project.name.ilike(f'%{keyword}%') | Project.description.ilike(f'%{keyword}%'))
        ).all()
        
        return jsonify([project.to_dict() for project in projects]), 200
        
    except SQLAlchemyError as e:
        return jsonify({'message': f'搜索项目失败: {str(e)}'}), 500


@projects_bp.route('/favorite/<int:project_id>', methods=['GET', 'POST'])
@token_required
def toggle_favorite(project_id):
    """
    收藏/取消收藏项目
    
    请求参数:
        action: 动作（可选，默认为添加收藏，值为"delete"表示取消收藏）
    
    返回:
        成功: {'message': '操作成功信息'}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取操作类型
    action = args.get('action')
    
    # 检查项目是否存在
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'message': '项目不存在'}), 404
    
    try:
        # 查找现有收藏记录
        favorite = UserFavorite.query.filter_by(
            user_id=request.user_id,
            project_id=project_id
        ).first()
        
        # 取消收藏
        if action == 'delete':
            if favorite:
                db.session.delete(favorite)
                db.session.commit()
                return jsonify({'message': '取消收藏成功'}), 200
            else:
                # 如果没有找到收藏记录，也返回成功
                return jsonify({'message': '项目未被收藏'}), 200
        
        # 添加收藏
        else:
            if favorite:
                # 如果已经收藏了，也返回成功
                return jsonify({'message': '项目已收藏'}), 200
            
            new_favorite = UserFavorite(
                user_id=request.user_id,
                project_id=project_id
            )
            db.session.add(new_favorite)
            db.session.commit()
            
            return jsonify({'message': '项目收藏成功'}), 200
            
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': f'操作失败: {str(e)}'}), 500


@projects_bp.route('/favorites', methods=['GET', 'POST'])
@token_required
def get_favorites():
    """
    获取收藏的项目列表
    
    请求参数:
        page: 页码（默认1）
        per_page: 每页数量（默认10）
    
    返回:
        成功: 项目列表分页数据
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
    
    try:
        # 通过关联表查询收藏的项目
        user_favorites = UserFavorite.query.filter_by(user_id=request.user_id).all()
        project_ids = [fav.project_id for fav in user_favorites]
        
        # 查询这些项目
        query = Project.query.filter(
            Project.id.in_(project_ids),
            Project.available == True
        )
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'items': [item.to_dict() for item in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({'message': f'查询收藏项目失败: {str(e)}'}), 500


@projects_bp.route('/exclusive/<int:project_id>', methods=['GET', 'POST'])
@token_required
def add_exclusive(project_id):
    """
    加入专属对接
    
    返回:
        成功: {'message': '加入专属对接成功'}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 检查项目是否存在
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'message': '项目不存在'}), 404
    
    # 检查项目是否为专属项目
    if not project.is_exclusive:
        return jsonify({'message': '非专属对接项目'}), 400
    
    try:
        # 查找现有专属对接记录
        exclusive = UserExclusiveProject.query.filter_by(
            user_id=request.user_id,
            project_id=project_id
        ).first()
        
        if exclusive:
            # 如果已经加入，直接返回成功
            return jsonify({'message': '已加入该专属对接'}), 200
        
        # 添加专属对接
        new_exclusive = UserExclusiveProject(
            user_id=request.user_id,
            project_id=project_id
        )
        db.session.add(new_exclusive)
        db.session.commit()
        
        return jsonify({'message': '加入专属对接成功'}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': f'加入专属对接失败: {str(e)}'}), 500


@projects_bp.route('/exclusive', methods=['GET', 'POST'])
@token_required
def get_exclusive_projects():
    """
    获取专属对接的项目列表
    
    请求参数:
        page: 页码（默认1）
        per_page: 每页数量（默认10）
    
    返回:
        成功: 项目列表分页数据
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
    
    try:
        # 通过关联表查询已加入的专属项目
        user_exclusives = UserExclusiveProject.query.filter_by(user_id=request.user_id).all()
        project_ids = [exc.project_id for exc in user_exclusives]
        
        # 查询这些项目
        query = Project.query.filter(
            Project.id.in_(project_ids),
            Project.available == True,
            Project.is_exclusive == True
        )
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'items': [item.to_dict() for item in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({'message': f'查询专属对接项目失败: {str(e)}'}), 500


@projects_bp.route('/all-exclusive', methods=['GET', 'POST'])
@token_required
def get_all_exclusive_projects():
    """
    获取所有可加入的专属项目
    
    请求参数:
        page: 页码（默认1）
        per_page: 每页数量（默认10）
    
    返回:
        成功: 项目列表分页数据
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
    
    try:
        # 查询所有专属项目
        query = Project.query.filter(
            Project.available == True,
            Project.is_exclusive == True
        )
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'items': [item.to_dict() for item in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({'message': f'查询专属项目失败: {str(e)}'}), 500


@projects_bp.route('/<int:project_id>', methods=['GET', 'POST'])
@token_required
def get_project_detail(project_id):
    """
    查询项目详情
    
    URL参数:
        project_id: 项目ID
    
    返回:
        成功: {'message': '获取项目详情成功', 'project': 项目详细信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 查询项目
    project = Project.query.get(project_id)
    
    if not project:
        return jsonify({'message': f'项目不存在: {project_id}'}), 404
    
    # 如果是专属项目，检查用户是否有权限访问
    user_id = request.user_id
    is_admin = request.is_admin
    
    # 初始化user_exclusive变量
    user_exclusive = None
    
    if project.is_exclusive and not is_admin:
        # 检查用户是否已加入该专属项目
        user_exclusive = UserExclusiveProject.query.filter_by(
            user_id=user_id,
            project_id=project_id
        ).first()
        
        if not user_exclusive:
            return jsonify({'message': '您没有权限访问此专属项目'}), 403
    
    # 获取基本信息
    project_data = project.to_dict()
    
    # 获取用户收藏状态
    user_favorite = UserFavorite.query.filter_by(
        user_id=user_id,
        project_id=project_id
    ).first()
    
    project_data['is_favorited'] = user_favorite is not None
    
    # 获取使用统计
    from sqlalchemy import func
    from app.models import PhoneNumber
    
    # 总使用量
    total_usage = db.session.query(func.count(PhoneNumber.id)).filter(
        PhoneNumber.project_id == project_id
    ).scalar() or 0
    
    # 用户使用量
    user_usage = db.session.query(func.count(PhoneNumber.id)).filter(
        PhoneNumber.project_id == project_id,
        PhoneNumber.user_id == user_id
    ).scalar() or 0
    
    # 成功率计算
    success_count = db.session.query(func.count(PhoneNumber.id)).filter(
        PhoneNumber.project_id == project_id,
        PhoneNumber.sms_code.isnot(None)
    ).scalar() or 0
    
    if total_usage > 0:
        success_rate = (success_count / total_usage) * 100
    else:
        success_rate = 0
    
    # 添加统计数据
    project_data['statistics'] = {
        'total_usage': total_usage,
        'user_usage': user_usage,
        'success_count': success_count,
        'success_rate': round(success_rate, 2)
    }
    
    # 添加相关操作链接
    token = request.args.get('token', '') if request.method == 'GET' else ''
    
    project_data['action_urls'] = {
        'get_number': f"{request.url_root}api/numbers/get?token={token}&project_code={project.code}",
        'favorite': f"{request.url_root}api/projects/favorite/{project_id}?token={token}",
        'unfavorite': f"{request.url_root}api/projects/favorite/{project_id}?token={token}&action=delete"
    }
    
    # 如果是专属项目且用户尚未加入，提供加入链接
    if project.is_exclusive and not user_exclusive and not is_admin:
        project_data['action_urls']['join_exclusive'] = f"{request.url_root}api/projects/exclusive/{project_id}?token={token}"
    
    return jsonify({
        'message': '获取项目详情成功',
        'project': project_data
    }), 200


@projects_bp.route('/batch-favorite', methods=['GET', 'POST'])
@token_required
def batch_favorite_projects():
    """
    批量收藏/取消收藏项目
    
    参数:
        token: 认证令牌
        project_ids: 项目ID列表，用逗号分隔
        action: 动作（可选，默认为添加收藏，值为"delete"表示取消收藏）
    
    返回:
        操作结果
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    # 获取请求参数
    project_ids_str = request.args.get('project_ids', '') or request.form.get('project_ids', '')
    action = request.args.get('action', '') or request.form.get('action', '')
    
    if not project_ids_str:
        return jsonify({
            'status': 'error',
            'message': '请提供项目ID列表'
        }), 400
    
    # 解析项目ID列表
    try:
        project_ids = [int(pid.strip()) for pid in project_ids_str.split(',') if pid.strip()]
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': '项目ID必须为整数'
        }), 400
    
    if not project_ids:
        return jsonify({
            'status': 'error',
            'message': '无效的项目ID列表'
        }), 400
    
    # 限制批量操作数量
    if len(project_ids) > 20:
        return jsonify({
            'status': 'error',
            'message': '一次最多操作20个项目'
        }), 400
    
    # 批量处理收藏/取消收藏
    results = {}
    for project_id in project_ids:
        # 查询项目
        project = Project.query.get(project_id)
        
        if not project:
            results[project_id] = {
                'status': 'error',
                'message': '项目不存在'
            }
            continue
        
        # 查询是否已收藏
        favorite = UserFavorite.query.filter_by(
            user_id=current_user_id,
            project_id=project_id
        ).first()
        
        # 执行收藏/取消收藏操作
        if action.lower() == 'delete':
            # 取消收藏
            if favorite:
                db.session.delete(favorite)
                results[project_id] = {
                    'status': 'success',
                    'message': '已取消收藏'
                }
            else:
                results[project_id] = {
                    'status': 'warning',
                    'message': '项目未收藏'
                }
        else:
            # 添加收藏
            if favorite:
                results[project_id] = {
                    'status': 'warning',
                    'message': '项目已收藏'
                }
            else:
                new_favorite = UserFavorite(
                    user_id=current_user_id,
                    project_id=project_id
                )
                db.session.add(new_favorite)
                results[project_id] = {
                    'status': 'success',
                    'message': '收藏成功'
                }
    
    # 提交数据库事务
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'results': results
    })


@projects_bp.route('/by-project-id/<string:project_id>', methods=['GET', 'POST'])
@token_required
def get_project_by_project_id(project_id):
    """
    通过项目ID(5位数字)查询项目信息
    
    URL参数:
        project_id: 5位数字项目ID
    
    返回:
        成功: {'message': '获取项目详情成功', 'project': 项目详细信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 查询项目
    project = Project.query.filter_by(project_id=project_id).first()
    
    if not project:
        return jsonify({'message': f'项目不存在: {project_id}'}), 404
    
    # 复用项目详情API的逻辑
    return get_project_detail(project.id)


@projects_bp.route('/by-exclusive-id/<string:exclusive_id>', methods=['GET', 'POST'])
@token_required
def get_project_by_exclusive_id(exclusive_id):
    """
    通过专属项目ID查询项目信息
    
    URL参数:
        exclusive_id: 专属项目ID (格式：XXXXX----xxxxxxxx)
    
    返回:
        成功: {'message': '获取项目详情成功', 'project': 项目详细信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 查询项目
    project = Project.query.filter_by(exclusive_id=exclusive_id).first()
    
    if not project:
        return jsonify({'message': f'专属项目不存在: {exclusive_id}'}), 404
    
    # 复用项目详情API的逻辑
    return get_project_detail(project.id)


@projects_bp.route('/exclusive/<int:project_id>/cancel', methods=['GET', 'POST'])
@token_required
def cancel_exclusive(project_id):
    """
    取消专属对接
    
    URL参数:
        project_id: 项目ID
    
    返回:
        成功: {'message': '取消专属对接成功'}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 检查项目是否存在
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'message': '项目不存在'}), 404
    
    # 检查项目是否为专属项目
    if not project.is_exclusive:
        return jsonify({'message': '非专属对接项目'}), 400
    
    try:
        # 查找现有专属对接记录
        exclusive = UserExclusiveProject.query.filter_by(
            user_id=request.user_id,
            project_id=project_id
        ).first()
        
        if not exclusive:
            # 如果没有找到对接记录，返回提示
            return jsonify({'message': '您未加入此专属对接'}), 400
        
        # 删除专属对接记录
        db.session.delete(exclusive)
        db.session.commit()
        
        return jsonify({'message': '取消专属对接成功'}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': f'取消专属对接失败: {str(e)}'}), 500 