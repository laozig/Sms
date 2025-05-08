from flask import Blueprint, request, jsonify
from app.models import db, PhoneNumber, Project, Transaction
from app.utils import token_required, admin_required, api_error_handler
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
import hashlib
import functools
import time

# 简单的内存缓存实现
class SimpleCache:
    def __init__(self, ttl=300):  # 默认缓存5分钟
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            value, expiry = self.cache[key]
            if expiry > time.time():
                return value
            else:
                # 缓存已过期，删除
                del self.cache[key]
        return None
    
    def set(self, key, value):
        expiry = time.time() + self.ttl
        self.cache[key] = (value, expiry)
    
    def clear(self):
        self.cache.clear()
    
    def prune_expired(self):
        """删除所有过期的缓存项"""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self.cache.items() if exp <= now]
        for k in expired_keys:
            del self.cache[k]

# 创建缓存实例
stats_cache = SimpleCache(ttl=300)  # 统计数据缓存5分钟

# 创建蓝图
statistics_bp = Blueprint('statistics', __name__)

def cached_stats(f):
    """缓存装饰器，用于缓存统计数据结果"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # 创建缓存键，基于请求参数和用户ID
        user_id = request.user_id
        is_admin = request.is_admin
        
        if request.method == 'GET':
            params = request.args.to_dict()
        else:
            params = request.json or {}
        
        # 为缓存键创建唯一字符串
        param_str = f"user:{user_id}:admin:{is_admin}:" + ":".join(f"{k}={v}" for k, v in sorted(params.items()))
        cache_key = hashlib.md5(param_str.encode()).hexdigest()
        
        # 尝试从缓存获取
        cached_result = stats_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 执行原函数
        result = f(*args, **kwargs)
        
        # 缓存结果（只缓存成功的结果）
        if isinstance(result, tuple) and len(result) >= 2 and result[1] == 200:
            stats_cache.set(cache_key, result)
        
        return result
    return wrapper

@statistics_bp.route('', methods=['GET', 'POST'])
@token_required
@api_error_handler
@cached_stats
def get_statistics():
    """
    获取统计数据
    
    请求参数:
        type: 统计类型(daily, weekly, monthly)
        start_date: 开始日期(YYYY-MM-DD)
        end_date: 结束日期(YYYY-MM-DD)
    
    返回:
        成功: {'message': '获取统计数据成功', 'statistics': 统计数据}
        失败: {'message': '错误信息'}, 错误状态码
    """
    # 支持GET和POST请求
    if request.method == 'GET':
        args = request.args
    else:
        args = request.json or {}
    
    # 获取参数
    stat_type = args.get('type', 'daily')
    start_date_str = args.get('start_date')
    end_date_str = args.get('end_date')
    
    # 验证参数
    if stat_type not in ['daily', 'weekly', 'monthly']:
        return jsonify({
            'message': '无效的统计类型',
            'help': '有效的统计类型: daily, weekly, monthly'
        }), 400
    
    try:
        # 设置默认日期范围（如果未提供）
        if not end_date_str:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        if not start_date_str:
            # 根据统计类型设置默认起始日期
            if stat_type == 'daily':
                start_date = end_date - timedelta(days=30)  # 30天
            elif stat_type == 'weekly':
                start_date = end_date - timedelta(weeks=12)  # 12周
            else:  # monthly
                start_date = end_date - timedelta(days=365)  # 12个月
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'message': '无效的日期格式，请使用YYYY-MM-DD格式'}), 400
    
    # 根据用户身份确定查询范围
    user_id = request.user_id
    is_admin = request.is_admin
    
    # 准备结果数据
    result = {
        'type': stat_type,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'statistics': {}
    }
    
    # 根据统计类型执行不同的查询
    if stat_type == 'daily':
        # 每日号码使用统计
        phone_stats = db.session.query(
            func.date(PhoneNumber.created_at).label('date'),
            func.count(PhoneNumber.id).label('count')
        )
        
        if not is_admin:
            phone_stats = phone_stats.filter(PhoneNumber.user_id == user_id)
        
        phone_stats = (phone_stats
            .filter(PhoneNumber.created_at.between(start_date, end_date))
            .group_by(func.date(PhoneNumber.created_at))
            .order_by(func.date(PhoneNumber.created_at))
            .all())
        
        # 每日消费统计
        spend_stats = db.session.query(
            func.date(Transaction.created_at).label('date'),
            func.sum(Transaction.amount).label('amount')
        )
        
        if not is_admin:
            spend_stats = spend_stats.filter(Transaction.user_id == user_id)
        
        spend_stats = (spend_stats
            .filter(Transaction.created_at.between(start_date, end_date))
            .filter(Transaction.type == 'consume')
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
            .all())
        
        # 格式化结果
        result['statistics']['phone_usage'] = [
            {'date': str(item.date), 'count': item.count} for item in phone_stats
        ]
        
        result['statistics']['spending'] = [
            {'date': str(item.date), 'amount': abs(float(item.amount))} for item in spend_stats
        ]
    
    elif stat_type == 'weekly':
        # 周统计逻辑
        # 提取周数
        phone_stats = db.session.query(
            func.strftime('%Y-%W', PhoneNumber.created_at).label('week'),
            func.count(PhoneNumber.id).label('count')
        )
        
        if not is_admin:
            phone_stats = phone_stats.filter(PhoneNumber.user_id == user_id)
        
        phone_stats = (phone_stats
            .filter(PhoneNumber.created_at.between(start_date, end_date))
            .group_by(func.strftime('%Y-%W', PhoneNumber.created_at))
            .order_by(func.strftime('%Y-%W', PhoneNumber.created_at))
            .all())
        
        # 周消费统计
        spend_stats = db.session.query(
            func.strftime('%Y-%W', Transaction.created_at).label('week'),
            func.sum(Transaction.amount).label('amount')
        )
        
        if not is_admin:
            spend_stats = spend_stats.filter(Transaction.user_id == user_id)
        
        spend_stats = (spend_stats
            .filter(Transaction.created_at.between(start_date, end_date))
            .filter(Transaction.type == 'consume')
            .group_by(func.strftime('%Y-%W', Transaction.created_at))
            .order_by(func.strftime('%Y-%W', Transaction.created_at))
            .all())
        
        # 格式化结果
        result['statistics']['phone_usage'] = [
            {'week': item.week, 'count': item.count} for item in phone_stats
        ]
        
        result['statistics']['spending'] = [
            {'week': item.week, 'amount': abs(float(item.amount))} for item in spend_stats
        ]
    
    else:  # monthly
        # 月度统计逻辑
        phone_stats = db.session.query(
            func.strftime('%Y-%m', PhoneNumber.created_at).label('month'),
            func.count(PhoneNumber.id).label('count')
        )
        
        if not is_admin:
            phone_stats = phone_stats.filter(PhoneNumber.user_id == user_id)
        
        phone_stats = (phone_stats
            .filter(PhoneNumber.created_at.between(start_date, end_date))
            .group_by(func.strftime('%Y-%m', PhoneNumber.created_at))
            .order_by(func.strftime('%Y-%m', PhoneNumber.created_at))
            .all())
        
        # 月度消费统计
        spend_stats = db.session.query(
            func.strftime('%Y-%m', Transaction.created_at).label('month'),
            func.sum(Transaction.amount).label('amount')
        )
        
        if not is_admin:
            spend_stats = spend_stats.filter(Transaction.user_id == user_id)
        
        spend_stats = (spend_stats
            .filter(Transaction.created_at.between(start_date, end_date))
            .filter(Transaction.type == 'consume')
            .group_by(func.strftime('%Y-%m', Transaction.created_at))
            .order_by(func.strftime('%Y-%m', Transaction.created_at))
            .all())
        
        # 格式化结果
        result['statistics']['phone_usage'] = [
            {'month': item.month, 'count': item.count} for item in phone_stats
        ]
        
        result['statistics']['spending'] = [
            {'month': item.month, 'amount': abs(float(item.amount))} for item in spend_stats
        ]
    
    # 添加项目使用统计
    project_stats = db.session.query(
        Project.name,
        Project.code,
        func.count(PhoneNumber.id).label('count')
    ).join(PhoneNumber, PhoneNumber.project_id == Project.id)
    
    if not is_admin:
        project_stats = project_stats.filter(PhoneNumber.user_id == user_id)
    
    project_stats = (project_stats
        .filter(PhoneNumber.created_at.between(start_date, end_date))
        .group_by(Project.id)
        .order_by(desc('count'))
        .all())
    
    result['statistics']['projects'] = [
        {'name': item.name, 'code': item.code, 'count': item.count} 
        for item in project_stats
    ]
    
    return jsonify({
        'message': '获取统计数据成功',
        'statistics': result
    }), 200 