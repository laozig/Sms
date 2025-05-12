from datetime import datetime
from flask import Blueprint, jsonify, request
from app.models import db
from app.utils import token_required, admin_required
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models import User

# 定义通知模型
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(20), default='info')  # info, warning, error, success
    is_read = Column(Boolean, default=False)
    is_global = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联用户
    user = relationship('User', backref='notifications')


# 定义通知设置模型
class NotificationSettings(db.Model):
    __tablename__ = 'notification_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    web_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联用户
    user = relationship('User', backref='notification_settings')

# 创建蓝图
notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET', 'POST'])
@token_required
def get_notifications():
    """
    获取用户通知列表
    
    参数:
        token: 认证令牌
        page: 页码（默认1）
        per_page: 每页数量（默认10）
        unread_only: 是否只返回未读通知（可选，默认false）
    
    返回:
        通知列表分页数据
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 50)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    # 构建查询
    query = Notification.query.filter(
        (Notification.user_id == current_user_id) | (Notification.is_global == True)
    )
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    # 分页
    pagination = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 格式化结果
    notifications = []
    for notification in pagination.items:
        notifications.append({
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'type': notification.type,
            'is_read': notification.is_read,
            'is_global': notification.is_global,
            'created_at': notification.created_at.isoformat()
        })
    
    return jsonify({
        'items': notifications,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })

@notifications_bp.route('/read/<int:notification_id>', methods=['GET', 'POST'])
@token_required
def mark_as_read(notification_id):
    """
    标记通知为已读
    
    参数:
        token: 认证令牌
        notification_id: 通知ID
    
    返回:
        操作结果
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({
            'status': 'error',
            'message': '通知不存在'
        }), 404
    
    # 检查权限（只能标记自己的通知或全局通知）
    if notification.user_id != current_user_id and not notification.is_global:
        return jsonify({
            'status': 'error',
            'message': '无权操作此通知'
        }), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '通知已标记为已读'
    })

@notifications_bp.route('/read-all', methods=['GET', 'POST'])
@token_required
def mark_all_as_read():
    """
    标记所有通知为已读
    
    参数:
        token: 认证令牌
    
    返回:
        操作结果
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    # 更新用户的所有通知和全局通知
    notifications = Notification.query.filter(
        (Notification.user_id == current_user_id) | (Notification.is_global == True)
    ).filter_by(is_read=False).all()
    
    count = 0
    for notification in notifications:
        notification.is_read = True
        count += 1
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'{count}条通知已标记为已读'
    })

@notifications_bp.route('/settings', methods=['GET', 'POST'])
@token_required
def get_notification_settings():
    """
    获取通知设置
    
    参数:
        token: 认证令牌
    
    返回:
        通知设置
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    # 获取用户的通知设置，如果不存在则创建
    settings = NotificationSettings.query.filter_by(user_id=current_user_id).first()
    
    if not settings:
        settings = NotificationSettings(user_id=current_user_id)
        db.session.add(settings)
        db.session.commit()
    
    return jsonify({
        'email_enabled': settings.email_enabled,
        'sms_enabled': settings.sms_enabled,
        'web_enabled': settings.web_enabled,
        'updated_at': settings.updated_at.isoformat()
    })

@notifications_bp.route('/settings/update', methods=['GET', 'POST'])
@token_required
def update_notification_settings():
    """
    更新通知设置
    
    参数:
        token: 认证令牌
        email_enabled: 是否启用邮件通知（可选）
        sms_enabled: 是否启用短信通知（可选）
        web_enabled: 是否启用网页通知（可选）
    
    返回:
        更新后的通知设置
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    # 获取请求参数
    data = request.get_json() if request.is_json else request.form
    
    # 获取用户的通知设置，如果不存在则创建
    settings = NotificationSettings.query.filter_by(user_id=current_user_id).first()
    
    if not settings:
        settings = NotificationSettings(user_id=current_user_id)
        db.session.add(settings)
    
    # 更新设置
    if 'email_enabled' in data:
        settings.email_enabled = data['email_enabled'] in [True, 'true', 1, '1']
    
    if 'sms_enabled' in data:
        settings.sms_enabled = data['sms_enabled'] in [True, 'true', 1, '1']
    
    if 'web_enabled' in data:
        settings.web_enabled = data['web_enabled'] in [True, 'true', 1, '1']
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '通知设置已更新',
        'settings': {
            'email_enabled': settings.email_enabled,
            'sms_enabled': settings.sms_enabled,
            'web_enabled': settings.web_enabled,
            'updated_at': settings.updated_at.isoformat()
        }
    })

@notifications_bp.route('/create', methods=['POST'])
@token_required
@admin_required
def create_notification():
    """
    创建新通知（仅管理员）
    
    参数:
        token: 认证令牌
        title: 通知标题
        content: 通知内容
        type: 通知类型（可选，默认info）
        is_global: 是否为全局通知（可选，默认false）
        user_id: 目标用户ID（可选，全局通知时忽略）
    
    返回:
        创建的通知信息
    """
    # 获取请求参数
    data = request.get_json() if request.is_json else request.form
    
    # 验证必填参数
    if 'title' not in data or 'content' not in data:
        return jsonify({
            'status': 'error',
            'message': '缺少必填参数'
        }), 400
    
    # 创建通知
    notification = Notification(
        title=data['title'],
        content=data['content'],
        type=data.get('type', 'info'),
        is_global=data.get('is_global') in [True, 'true', 1, '1']
    )
    
    # 如果不是全局通知，则需要指定用户
    if not notification.is_global:
        if 'user_id' not in data:
            return jsonify({
                'status': 'error',
                'message': '非全局通知需要指定用户ID'
            }), 400
        
        notification.user_id = int(data['user_id'])
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '通知创建成功',
        'notification': {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'type': notification.type,
            'is_global': notification.is_global,
            'user_id': notification.user_id,
            'created_at': notification.created_at.isoformat()
        }
    }), 201

@notifications_bp.route('/delete/<int:notification_id>', methods=['GET', 'POST'])
@token_required
def delete_notification(notification_id):
    """
    删除通知
    
    参数:
        token: 认证令牌
        notification_id: 通知ID
    
    返回:
        操作结果
    """
    # 从request中获取当前用户信息
    current_user_id = request.user_id
    is_admin = request.is_admin
    
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({
            'status': 'error',
            'message': '通知不存在'
        }), 404
    
    # 检查权限（只能删除自己的通知，管理员可删除任何通知）
    if notification.user_id != current_user_id and not is_admin:
        return jsonify({
            'status': 'error',
            'message': '无权删除此通知'
        }), 403
    
    db.session.delete(notification)
    db.session.commit()
    
    
    return jsonify({
        'status': 'success',
        'message': '通知已删除'

    }) 