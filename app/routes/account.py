from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from app.models import db, User, Transaction
from app.utils import token_required, admin_required, SMSApiClient, validate_pagination_params

# 创建蓝图
account_bp = Blueprint('account', __name__)


@account_bp.route('/balance', methods=['GET'])
@token_required
def get_balance():
    """
    获取账户余额
    
    请求头:
        Authorization: Bearer <token>
    
    返回:
        成功: {'balance': 余额}
        失败: {'message': '错误信息'}, 错误状态码
    """
    user = User.query.get(request.user_id)
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 调用API查询余额（上游平台）
    client = SMSApiClient()
    api_result = client.check_balance()
    
    if not api_result.get('success', False):
        # 如果API查询失败，返回数据库中的余额
        return jsonify({'balance': user.balance}), 200
    
    # 如果API查询成功，更新并返回余额
    try:
        api_balance = api_result.get('data', {}).get('balance', user.balance)
        
        # 更新本地余额（如果与API返回的余额不同）
        if api_balance != user.balance:
            user.balance = api_balance
            db.session.commit()
        
        return jsonify({'balance': api_balance}), 200
    except Exception as e:
        return jsonify({'message': f'更新余额失败: {str(e)}'}), 500


@account_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions():
    """
    获取交易记录
    
    请求头:
        Authorization: Bearer <token>
    
    查询参数:
        page: 页码 (默认: 1)
        per_page: 每页数量 (默认: 10)
        type: 交易类型过滤 (可选: topup, consume, refund)
        
    返回:
        成功: {
            'items': 交易记录列表,
            'total': 总数量,
            'page': 当前页码,
            'per_page': 每页数量,
            'pages': 总页数
        }
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config.get('ITEMS_PER_PAGE', 10), type=int)
    transaction_type = request.args.get('type')
    
    # 验证分页参数
    page, per_page = validate_pagination_params(page, per_page)
    
    # 构建查询
    query = Transaction.query.filter_by(user_id=request.user_id)
    
    # 应用类型过滤
    if transaction_type:
        query = query.filter_by(type=transaction_type)
    
    # 分页查询
    paginated_transactions = query.order_by(Transaction.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # 准备响应数据
    response = {
        'items': [t.to_dict() for t in paginated_transactions.items],
        'total': paginated_transactions.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated_transactions.pages
    }
    
    return jsonify(response), 200


@account_bp.route('/topup', methods=['GET', 'POST'])
@token_required
def topup_account():
    """
    充值账户余额
    
    请求头:
        Authorization: Bearer <token>
    
    请求参数:
        amount: 充值金额
        payment_method: 支付方式 (如: alipay, wechat)
        
    返回:
        成功: {'message': '充值成功', 'balance': 当前余额}
        失败: {'message': '错误信息'}, 错误状态码
    """
    if request.method == 'GET':
        # 从查询参数获取金额和支付方式
        amount = request.args.get('amount')
        payment_method = request.args.get('payment_method', 'default')
        
        if not amount:
            return jsonify({'message': '请通过POST请求充值，或在GET请求中提供amount参数'}), 400
    else:
        # 从POST请求体获取金额和支付方式
        data = request.get_json() or request.form.to_dict()
        
        # 检查必要字段
        if not all(k in data for k in ('amount', 'payment_method')):
            return jsonify({'message': '缺少必要的字段'}), 400
        
        amount = data.get('amount')
        payment_method = data.get('payment_method')
    
    # 验证金额
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'message': '充值金额必须大于0'}), 400
    except (TypeError, ValueError):
        return jsonify({'message': '无效的金额格式'}), 400
    
    # 查找用户
    user = User.query.get(request.user_id)
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 处理充值（这里应该集成实际的支付系统，但为了简化，我们直接增加余额）
    try:
        # 更新余额
        new_balance = user.balance + amount
        user.balance = new_balance
        
        # 创建交易记录
        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            balance=new_balance,
            type='topup',
            description=f'通过{payment_method}充值',
            reference_id=f'topup-{user.id}-{int(datetime.utcnow().timestamp())}'
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': '充值成功',
            'balance': new_balance
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'充值失败: {str(e)}'}), 500


@account_bp.route('/create-order', methods=['GET', 'POST'])
@token_required
def create_order():
    """
    创建充值订单
    
    请求参数:
        amount: 充值金额
        payment_method: 支付方式（如：alipay, wechat, card）
        coupon_code: 优惠券代码（可选）
    
    返回:
        成功: {'message': '订单创建成功', 'order': 订单信息和支付链接}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取参数
    amount = args.get('amount')
    payment_method = args.get('payment_method')
    coupon_code = args.get('coupon_code')
    
    # 验证参数
    if not amount:
        return jsonify({
            'message': '请提供充值金额',
            'help': '示例请求: /api/account/create-order?token=您的令牌&amount=100&payment_method=alipay'
        }), 400
    
    if not payment_method:
        return jsonify({
            'message': '请提供支付方式',
            'help': '有效的支付方式: alipay, wechat, card'
        }), 400
    
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'message': '充值金额必须大于0'}), 400
    except ValueError:
        return jsonify({'message': '无效的充值金额'}), 400
    
    # 检查支付方式是否有效
    valid_payment_methods = ['alipay', 'wechat', 'card']
    if payment_method not in valid_payment_methods:
        return jsonify({
            'message': f'无效的支付方式: {payment_method}',
            'valid_methods': valid_payment_methods
        }), 400
    
    # 生成订单ID
    import uuid
    import time
    order_id = f"order_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    # 查找用户
    user = User.query.get(request.user_id)
    
    # 处理优惠券
    discount = 0
    if coupon_code:
        # 在实际应用中，应该查询数据库验证优惠券
        # 这里简单模拟
        if coupon_code == 'WELCOME10':
            discount = amount * 0.1  # 10%折扣
    
    # 最终金额
    final_amount = amount - discount
    
    # 创建交易记录(类型为pending)
    transaction = Transaction(
        user_id=user.id,
        amount=final_amount,  # 记录为正值，表示待处理的充值
        balance=user.balance,  # 当前余额(未变更)
        type='pending',
        description=f'充值订单(使用{payment_method}支付)',
        reference_id=order_id
    )
    
    try:
        db.session.add(transaction)
        db.session.commit()
        
        # 生成支付链接
        payment_url = f"http://example.com/pay/{payment_method}/{order_id}"
        
        return jsonify({
            'message': '订单创建成功',
            'order': {
                'order_id': order_id,
                'amount': amount,
                'discount': discount,
                'final_amount': final_amount,
                'payment_method': payment_method,
                'status': 'pending',
                'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'payment_url': payment_url
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'创建订单失败: {str(e)}'}), 500


@account_bp.route('/order-status/<order_id>', methods=['GET', 'POST'])
@token_required
def check_order_status(order_id):
    """
    查询充值订单状态
    
    URL参数:
        order_id: 订单ID
    
    返回:
        成功: {'message': '订单状态查询成功', 'order': 订单状态信息}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 查询交易记录
    transaction = Transaction.query.filter_by(
        reference_id=order_id,
        user_id=request.user_id
    ).first()
    
    if not transaction:
        return jsonify({'message': f'未找到订单: {order_id}'}), 404
    
    # 构建订单状态
    order_status = {
        'order_id': transaction.reference_id,
        'amount': abs(transaction.amount),
        'status': 'completed' if transaction.type == 'topup' else 'pending',
        'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 如果是已完成的订单，增加完成时间
    if transaction.type == 'topup':
        order_status['completed_at'] = transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    
    # 模拟支付处理
    # 在实际应用中，这里应该查询支付网关的API
    # 这里简单模拟一个随机完成的过程
    import random
    
    # 如果订单状态是pending，有30%的概率被标记为已完成
    if transaction.type == 'pending' and random.random() < 0.3:
        # 更新交易记录
        transaction.type = 'topup'
        transaction.updated_at = datetime.utcnow()
        # 更新用户余额
        user = User.query.get(request.user_id)
        user.balance += abs(transaction.amount)
        
        try:
            db.session.commit()
            # 更新返回状态
            order_status['status'] = 'completed'
            order_status['completed_at'] = transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'更新订单状态失败: {str(e)}'}), 500
    
    return jsonify({
        'message': '订单状态查询成功',
        'order': order_status
    }), 200 