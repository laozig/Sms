from flask import Blueprint, request, jsonify
from app.models import db, User, Project, PhoneNumber, Transaction, BlacklistedNumber
from app.utils import token_required, admin_required
from sqlalchemy import or_, func
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# 用户列表、分页、搜索
@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def admin_get_users():
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    keyword = request.args.get('keyword', '')
    query = User.query
    if keyword:
        query = query.filter(or_(User.username.ilike(f'%{keyword}%'), User.email.ilike(f'%{keyword}%')))
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users = [u.to_dict() for u in pagination.items]
    return jsonify({
        'items': users,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })

# 用户详情
@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def admin_get_user_detail(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    return jsonify({'user': user.to_dict()})

# 新建用户
@admin_bp.route('/users', methods=['POST'])
@token_required
@admin_required
def admin_create_user():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    is_admin = data.get('is_admin', False)
    if not username or not email or not password:
        return jsonify({'message': '缺少必要参数'}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'message': '用户名或邮箱已存在'}), 400
    user = User(username=username, email=email, password=password, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': '用户创建成功', 'user': user.to_dict()}), 201

# 修改用户
@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def admin_update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    data = request.get_json() or {}
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    if 'password' in data:
        user.password = data['password']
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    if 'is_active' in data:
        user.is_active = data['is_active']
    db.session.commit()
    return jsonify({'message': '用户信息已更新', 'user': user.to_dict()})

# 删除/禁用用户
@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    user.is_active = False
    db.session.commit()
    return jsonify({'message': '用户已禁用'})

# 项目列表
@admin_bp.route('/projects', methods=['GET'])
@token_required
@admin_required
def admin_get_projects():
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    keyword = request.args.get('keyword', '')
    query = Project.query
    if keyword:
        query = query.filter(or_(Project.name.ilike(f'%{keyword}%'), Project.code.ilike(f'%{keyword}%')))
    pagination = query.order_by(Project.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    projects = [p.to_dict() for p in pagination.items]
    return jsonify({
        'items': projects,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })

# 新建项目
@admin_bp.route('/projects', methods=['POST'])
@token_required
@admin_required
def admin_create_project():
    data = request.get_json() or {}
    name = data.get('name')
    code = data.get('code')
    price = data.get('price')
    is_exclusive = data.get('is_exclusive', False)
    
    if not name or not code or price is None:
        return jsonify({'message': '缺少必要参数'}), 400
    if Project.query.filter_by(code=code).first():
        return jsonify({'message': '项目代码已存在'}), 400
    
    # 创建项目，自动生成项目ID和专属项目ID（如果是专属项目）
    project = Project(
        name=name, 
        code=code, 
        price=price,
        description=data.get('description', ''),
        is_exclusive=is_exclusive
    )
    
    project.success_rate = data.get('success_rate', 0.0)
    project.available = data.get('available', True)
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify({
        'message': '项目创建成功', 
        'project': project.to_dict()
    }), 201

# 修改项目
@admin_bp.route('/projects/<int:project_id>', methods=['PUT'])
@token_required
@admin_required
def admin_update_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'message': '项目不存在'}), 404
    
    data = request.get_json() or {}
    project.name = data.get('name', project.name)
    project.code = data.get('code', project.code)
    project.price = data.get('price', project.price)
    project.description = data.get('description', project.description)
    project.success_rate = data.get('success_rate', project.success_rate)
    project.available = data.get('available', project.available)
    
    # 检查专属项目状态是否改变
    if 'is_exclusive' in data and data['is_exclusive'] != project.is_exclusive:
        # 使用自定义方法处理专属项目ID的变更
        project.set_exclusive(data['is_exclusive'])
    
    db.session.commit()
    return jsonify({'message': '项目信息已更新', 'project': project.to_dict()})

# 删除项目
@admin_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@token_required
@admin_required
def admin_delete_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'message': '项目不存在'}), 404
    
    # 先删除与项目相关的收藏记录
    from app.models import UserFavorite
    UserFavorite.query.filter_by(project_id=project_id).delete()
    
    # 删除与项目相关的专属对接记录
    from app.models import UserExclusiveProject
    UserExclusiveProject.query.filter_by(project_id=project_id).delete()
    
    # 最后删除项目
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': '项目已删除'})

# 号码管理：列表、搜索、导出、修改、删除
@admin_bp.route('/numbers', methods=['GET'])
@token_required
@admin_required
def admin_get_numbers():
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    query = PhoneNumber.query
    if keyword:
        query = query.filter(PhoneNumber.number.ilike(f'%{keyword}%'))
    if status:
        query = query.filter(PhoneNumber.status == status)
    pagination = query.order_by(PhoneNumber.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    numbers = [n.to_dict() for n in pagination.items]
    return jsonify({
        'items': numbers,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })

@admin_bp.route('/numbers/<int:number_id>', methods=['PUT'])
@token_required
@admin_required
def admin_update_number(number_id):
    number = PhoneNumber.query.get(number_id)
    if not number:
        return jsonify({'message': '号码不存在'}), 404
    data = request.get_json() or {}
    number.status = data.get('status', number.status)
    db.session.commit()
    return jsonify({'message': '号码信息已更新', 'number': number.to_dict()})

@admin_bp.route('/numbers/<int:number_id>', methods=['DELETE'])
@token_required
@admin_required
def admin_delete_number(number_id):
    number = PhoneNumber.query.get(number_id)
    if not number:
        return jsonify({'message': '号码不存在'}), 404
    db.session.delete(number)
    db.session.commit()
    return jsonify({'message': '号码已删除'})

# 通知管理
from app.routes.notifications import Notification

@admin_bp.route('/notifications', methods=['GET'])
@token_required
@admin_required
def admin_get_notifications():
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    query = Notification.query
    pagination = query.order_by(Notification.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    notifications = []
    for n in pagination.items:
        notifications.append({
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'type': n.type,
            'is_read': n.is_read,
            'is_global': n.is_global,
            'user_id': n.user_id,
            'created_at': n.created_at.isoformat()
        })
    return jsonify({
        'items': notifications,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })

@admin_bp.route('/notifications', methods=['POST'])
@token_required
@admin_required
def admin_create_notification():
    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')
    type_ = data.get('type', 'info')
    is_global = data.get('is_global', False)
    user_id = data.get('user_id')
    if not title or not content:
        return jsonify({'message': '缺少必要参数'}), 400
    from app.routes.notifications import Notification
    notification = Notification(
        title=title,
        content=content,
        type=type_,
        is_global=is_global
    )
    if not is_global and user_id:
        notification.user_id = user_id
    db.session.add(notification)
    db.session.commit()
    return jsonify({'message': '通知创建成功', 'notification_id': notification.id}), 201

@admin_bp.route('/notifications/<int:notification_id>', methods=['PUT'])
@token_required
@admin_required
def admin_update_notification(notification_id):
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'message': '通知不存在'}), 404
    data = request.get_json() or {}
    notification.title = data.get('title', notification.title)
    notification.content = data.get('content', notification.content)
    notification.type = data.get('type', notification.type)
    notification.is_global = data.get('is_global', notification.is_global)
    db.session.commit()
    return jsonify({'message': '通知已更新'})

@admin_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@token_required
@admin_required
def admin_delete_notification(notification_id):
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'message': '通知不存在'}), 404
    db.session.delete(notification)
    db.session.commit()
    return jsonify({'message': '通知已删除'})

# 统计管理（全局统计）
@admin_bp.route('/statistics', methods=['GET'])
@token_required
@admin_required
def admin_statistics():
    user_count = User.query.count()
    project_count = Project.query.count()
    number_count = PhoneNumber.query.count()
    transaction_count = Transaction.query.count()
    total_balance = db.session.query(func.sum(User.balance)).scalar() or 0
    total_income = db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == 'topup').scalar() or 0
    total_consume = db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == 'consume').scalar() or 0
    return jsonify({
        'user_count': user_count,
        'project_count': project_count,
        'number_count': number_count,
        'transaction_count': transaction_count,
        'total_balance': total_balance,
        'total_income': total_income,
        'total_consume': abs(total_consume)
    })

# 操作日志管理
class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    level = db.Column(db.String(20), default='info')  # info, warning, error, debug
    content = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联用户
    user = db.relationship('User', backref='admin_logs')

@admin_bp.route('/logs', methods=['GET'])
@token_required
@admin_required
def admin_get_logs():
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    
    query = AdminLog.query
    pagination = query.order_by(AdminLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    logs = []
    for log in pagination.items:
        user_info = None
        if log.user:
            user_info = {
                'id': log.user.id,
                'username': log.user.username
            }
        
        logs.append({
            'id': log.id,
            'level': log.level,
            'content': log.content,
            'ip_address': log.ip_address,
            'user': user_info,
            'created_at': log.created_at.isoformat()
        })
    
    return jsonify({
        'items': logs,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })

@admin_bp.route('/logs', methods=['POST'])
@token_required
@admin_required
def admin_create_log():
    data = request.get_json() or {}
    
    if 'content' not in data:
        return jsonify({'message': '缺少必要参数'}), 400
    
    log = AdminLog(
        content=data['content'],
        level=data.get('level', 'info'),
        user_id=request.user_id,
        ip_address=request.remote_addr
    )
    
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': '日志创建成功', 'log_id': log.id}), 201 