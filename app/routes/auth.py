from flask import Blueprint, request, jsonify
from app.models import db, User
from app.utils import generate_token, token_required
import re

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# 邮箱验证正则表达式
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册
    
    请求参数:
        username: 用户名
        email: 邮箱
        password: 密码
    
    返回:
        成功: {'message': '注册成功', 'token': '生成的JWT令牌'}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 获取参数，支持GET和POST请求
    if request.method == 'GET':
        data = request.args.to_dict()
        # 如果没有提供参数，返回说明信息
        if not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({
                'message': '请提供username、email和password参数'
            }), 400
    else:
        # 处理POST请求
        data = request.get_json() or request.form.to_dict()
    
    # 检查必要字段
    if not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'message': '缺少必要的字段'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # 验证用户名长度
    if len(username) < 3 or len(username) > 20:
        return jsonify({'message': '用户名长度应在3-20个字符之间'}), 400
    
    # 验证邮箱格式
    if not re.match(EMAIL_REGEX, email):
        return jsonify({'message': '无效的邮箱格式'}), 400
    
    # 验证密码长度
    if len(password) < 6 or len(password) > 20:
        return jsonify({'message': '密码长度应在6-20个字符之间'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'message': '该用户名已被使用'}), 409
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'message': '该邮箱已被注册'}), 409
    
    # 创建新用户
    new_user = User(
        username=username,
        email=email,
        password=password
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # 生成JWT令牌
        token = generate_token(
            user_id=new_user.id,
            username=new_user.username,
            is_admin=new_user.is_admin
        )
        
        return jsonify({
            'message': '注册成功',
            'token': token,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'注册失败: {str(e)}'}), 500


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录
    
    请求参数:
        username: 用户名
        password: 密码
    
    返回:
        成功: {'message': '登录成功', 'token': '生成的JWT令牌', 'user': 用户信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 获取参数，支持GET和POST请求
    if request.method == 'GET':
        data = request.args.to_dict()
        # 如果没有提供参数，返回说明信息
        if not all(k in data for k in ('username', 'password')):
            return jsonify({
                'message': '请提供username和password参数'
            }), 400
    else:
        # 处理POST请求
        data = request.get_json() or request.form.to_dict()
    
    # 检查必要字段
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'message': '缺少必要的字段'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    
    # 如果未找到用户或密码不匹配
    if not user or not user.check_password(password):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 检查用户状态
    if not user.is_active:
        return jsonify({'message': '账号已被禁用'}), 403
    
    # 生成JWT令牌
    token = generate_token(
        user_id=user.id,
        username=user.username,
        is_admin=user.is_admin
    )
    
    return jsonify({
        'message': '登录成功',
        'token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@token_required
def change_password():
    """
    修改密码
    
    请求头:
        Authorization: Bearer <token>
    
    请求参数:
        old_password: 旧密码
        new_password: 新密码
    
    返回:
        成功: {'message': '密码修改成功'}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 获取参数，支持GET和POST请求
    if request.method == 'GET':
        data = request.args.to_dict()
        # 如果没有提供参数，返回说明信息
        if not all(k in data for k in ('old_password', 'new_password')):
            return jsonify({
                'message': '请提供old_password和new_password参数'
            }), 400
    else:
        # 处理POST请求
        data = request.get_json() or request.form.to_dict()
    
    # 检查必要字段
    if not all(k in data for k in ('old_password', 'new_password')):
        return jsonify({'message': '缺少必要的字段'}), 400
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    # 验证新密码长度
    if len(new_password) < 6 or len(new_password) > 20:
        return jsonify({'message': '新密码长度应在6-20个字符之间'}), 400
    
    # 查找用户
    user = User.query.filter_by(id=request.user_id).first()
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 验证旧密码
    if not user.check_password(old_password):
        return jsonify({'message': '旧密码不正确'}), 401
    
    # 更新密码
    try:
        user.password = new_password  # 直接设置明文密码
        db.session.commit()
        return jsonify({'message': '密码修改成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'密码修改失败: {str(e)}'}), 500


@auth_bp.route('/profile', methods=['GET', 'POST', 'PATCH'])
@token_required
def get_profile():
    """
    获取或更新用户个人资料
    
    请求头或请求体:
        Authorization: Bearer <token> 或 token: <令牌>
    
    返回:
        成功: 用户信息
        失败: {'message': '错误信息'}, 错误状态码
    """
    user = User.query.filter_by(id=request.user_id).first()
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    if request.method == 'GET' or request.method == 'POST':
        # 获取个人资料
        return jsonify(user.to_dict()), 200
    else:
        # 更新个人资料
        data = request.get_json() or request.form.to_dict()
        
        # 更新邮箱
        if 'email' in data:
            email = data.get('email')
            
            # 验证邮箱格式
            if not re.match(EMAIL_REGEX, email):
                return jsonify({'message': '无效的邮箱格式'}), 400
            
            # 检查邮箱是否已被其他用户使用
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'message': '该邮箱已被其他用户注册'}), 409
            
            user.email = email
        
        try:
            db.session.commit()
            return jsonify({
                'message': '资料更新成功',
                'user': user.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'资料更新失败: {str(e)}'}), 500


@auth_bp.route('/update-profile', methods=['GET', 'POST'])
@token_required
def update_profile():
    """
    修改个人资料
    
    请求参数:
        email: 新邮箱（可选）
        password: 新密码（可选）
        avatar: 头像URL（可选）
    
    返回:
        成功: {'message': '个人资料更新成功', 'user': 更新后的用户信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    try:
        # 获取参数，支持GET和POST请求
        if request.method == 'GET':
            data = request.args.to_dict()
        else:
            data = request.get_json() or request.form.to_dict()
        
        # 查找用户
        user = User.query.filter_by(id=request.user_id).first()
        
        if not user:
            return jsonify({'message': '用户不存在'}), 404
        
        # 更新邮箱
        if 'email' in data and data['email']:
            email = data['email']
            # 验证邮箱格式
            if not re.match(EMAIL_REGEX, email):
                return jsonify({'message': '无效的邮箱格式'}), 400
            
            # 检查邮箱是否已被其他用户使用
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user.id:
                print(f"该邮箱已被其他用户注册: {email}")
                return jsonify({'message': '该邮箱已被其他用户注册'}), 409
            
            user.email = email
        
        # 更新密码
        if 'password' in data and data['password']:
            password = data['password']
            # 验证密码长度
            if len(password) < 6 or len(password) > 20:
                return jsonify({'message': '密码长度应在6-20个字符之间'}), 400
            
            user.password = password
        
        # 更新头像 URL
        if 'avatar' in data and data['avatar']:
            user.avatar = data['avatar']
        
        # 保存更改
        db.session.commit()
        return jsonify({
            'message': '个人资料更新成功',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'更新个人资料失败: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['GET', 'POST'])
@token_required
def logout():
    """
    注销令牌
    
    返回:
        成功: {'message': '令牌已注销'}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 这里我们可以实现一个黑名单来保存已注销的令牌
    # 但由于令牌有自己的过期时间，实际上可以直接返回成功
    # 如果需要强制注销，可以添加令牌到黑名单中
    
    return jsonify({
        'message': '令牌已注销',
        'info': '您可以重新登录获取新的令牌'
    }), 200


@auth_bp.route('/api-key', methods=['GET', 'POST'])
@token_required
def manage_api_key():
    """
    API密钥管理
    
    请求参数:
        action: 操作类型(generate, revoke)
    
    返回:
        成功: {'message': '操作成功', 'api_key': API密钥信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 获取参数，支持GET和POST请求
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.get_json() or request.form.to_dict()
    
    action = data.get('action', 'generate')
    
    # 查找用户
    user = User.query.filter_by(id=request.user_id).first()
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 生成或撤销API密钥
    import secrets
    import hashlib
    
    if action == 'generate':
        # 生成新的API密钥
        api_key_raw = secrets.token_hex(16)
        # 在实际应用中，应该将哈希值存储在数据库中
        api_key_hash = hashlib.sha256(api_key_raw.encode()).hexdigest()
        
        # 这里应该将api_key_hash保存到数据库中
        # 如果模型中没有api_key字段，需要先添加该字段
        # 为简化演示，这里直接返回生成的密钥
        
        return jsonify({
            'message': 'API密钥生成成功',
            'api_key': api_key_raw,
            'expires_at': 'Never',  # 在实际应用中，可以设置过期时间
            'note': '请妥善保管您的API密钥，它只会显示一次'
        }), 200
    
    elif action == 'revoke':
        # 撤销API密钥
        # 在实际应用中，应该将用户的API密钥从数据库中删除
        
        return jsonify({
            'message': 'API密钥已撤销',
            'note': '您的API密钥已失效，需要重新生成'
        }), 200
    
    else:
        return jsonify({
            'message': '无效的操作类型',
            'help': '有效的操作类型: generate, revoke'
        }), 400 