from flask import Blueprint, request, jsonify, make_response, current_app
from app.models import db, PhoneNumber, Project, Transaction, User, PhoneRequest, SMS
from app.utils import token_required, admin_required, api_error_handler, validate_pagination_params
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
import hashlib
import functools
import time
import json
import csv
from io import StringIO
from io import BytesIO
from flask import make_response
import pandas as pd
from openpyxl.utils import get_column_letter

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

@statistics_bp.route('/custom', methods=['GET', 'POST'])
@token_required
def custom_statistics():
    """
    自定义统计数据
    
    参数:
        token: 认证令牌
        start_date: 开始日期(YYYY-MM-DD)
        end_date: 结束日期(YYYY-MM-DD)
        metrics: 要统计的指标，多个用逗号分隔
                可选值：sms_count, success_rate, avg_response_time, 
                      cost, project_distribution, hourly_activity
        project_code: 项目代码过滤（可选）
        
    返回:
        自定义统计数据
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    # 获取请求参数
    try:
        start_date_str = request.args.get('start_date') or request.form.get('start_date')
        end_date_str = request.args.get('end_date') or request.form.get('end_date')
        metrics_str = request.args.get('metrics') or request.form.get('metrics', '')
        project_code = request.args.get('project_code') or request.form.get('project_code')
        
        if not start_date_str or not end_date_str:
            return jsonify({
                'status': 'error',
                'message': '请提供开始和结束日期'
            }), 400
        
        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        
        # 检查日期范围
        date_range = (end_date - start_date).days
        if date_range < 0:
            return jsonify({
                'status': 'error',
                'message': '结束日期必须大于等于开始日期'
            }), 400
        
        if date_range > 90:
            return jsonify({
                'status': 'error',
                'message': '日期范围不能超过90天'
            }), 400
        
        # 解析指标
        metrics = [m.strip() for m in metrics_str.split(',') if m.strip()]
        valid_metrics = ['sms_count', 'success_rate', 'avg_response_time', 
                         'cost', 'project_distribution', 'hourly_activity']
        
        if not metrics:
            metrics = valid_metrics  # 默认统计所有指标
        else:
            # 验证指标有效性
            invalid_metrics = [m for m in metrics if m not in valid_metrics]
            if invalid_metrics:
                return jsonify({
                    'status': 'error',
                    'message': f'无效的指标: {", ".join(invalid_metrics)}'
                }), 400
        
        # 构建查询基础
        base_query = PhoneRequest.query.filter(
            PhoneRequest.user_id == current_user_id,
            PhoneRequest.created_at.between(start_date, end_date)
        )
        
        if project_code:
            project = Project.query.filter_by(code=project_code).first()
            if project:
                base_query = base_query.filter(PhoneRequest.project_id == project.id)
        
        # 统计结果
        result = {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days': date_range + 1
            },
            'metrics': {}
        }
        
        # 统计各个指标
        if 'sms_count' in metrics:
            # 短信数量统计
            sms_count = base_query.count()
            sms_received = db.session.query(func.count(SMS.id)).join(
                PhoneRequest, SMS.phone_request_id == PhoneRequest.id
            ).filter(
                PhoneRequest.user_id == current_user_id,
                PhoneRequest.created_at.between(start_date, end_date)
            )
            
            if project_code and project:
                sms_received = sms_received.filter(PhoneRequest.project_id == project.id)
                
            result['metrics']['sms_count'] = {
                'total_requests': sms_count,
                'received_sms': sms_received.scalar() or 0
            }
        
        if 'success_rate' in metrics:
            # 成功率统计
            total_requests = base_query.count()
            successful_requests = base_query.filter(PhoneRequest.status.in_(['used', 'completed'])).count()
            
            success_rate = 0
            if total_requests > 0:
                success_rate = (successful_requests / total_requests) * 100
                
            result['metrics']['success_rate'] = {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'rate': round(success_rate, 2)
            }
        
        if 'avg_response_time' in metrics:
            # 平均响应时间统计
            response_times = db.session.query(
                func.avg(func.extract('epoch', SMS.received_at - PhoneRequest.created_at))
            ).join(
                PhoneRequest, SMS.phone_request_id == PhoneRequest.id
            ).filter(
                PhoneRequest.user_id == current_user_id,
                PhoneRequest.created_at.between(start_date, end_date)
            )
            
            if project_code and project:
                response_times = response_times.filter(PhoneRequest.project_id == project.id)
                
            avg_time = response_times.scalar() or 0
            
            result['metrics']['avg_response_time'] = {
                'seconds': round(avg_time, 2),
                'formatted': f"{int(avg_time // 60)}分{int(avg_time % 60)}秒"
            }
        
        if 'cost' in metrics:
            # 消费统计
            total_cost = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user_id,
                Transaction.type == 'consume',
                Transaction.created_at.between(start_date, end_date)
            ).scalar() or 0
            
            result['metrics']['cost'] = {
                'total': abs(total_cost),
                'daily_average': round(abs(total_cost) / (date_range + 1), 2)
            }
        
        if 'project_distribution' in metrics:
            # 项目分布统计
            project_stats = db.session.query(
                Project.name, Project.code, func.count(PhoneRequest.id)
            ).join(
                PhoneRequest, Project.id == PhoneRequest.project_id
            ).filter(
                PhoneRequest.user_id == current_user_id,
                PhoneRequest.created_at.between(start_date, end_date)
            ).group_by(
                Project.id
            ).all()
            
            projects = []
            for name, code, count in project_stats:
                projects.append({
                    'name': name,
                    'code': code,
                    'count': count
                })
            
            result['metrics']['project_distribution'] = projects
        
        if 'hourly_activity' in metrics:
            # 按小时活跃度统计
            hourly_stats = db.session.query(
                func.extract('hour', PhoneRequest.created_at), 
                func.count(PhoneRequest.id)
            ).filter(
                PhoneRequest.user_id == current_user_id,
                PhoneRequest.created_at.between(start_date, end_date)
            )
            
            if project_code and project:
                hourly_stats = hourly_stats.filter(PhoneRequest.project_id == project.id)
                
            hourly_stats = hourly_stats.group_by(
                func.extract('hour', PhoneRequest.created_at)
            ).all()
            
            hours = [0] * 24
            for hour, count in hourly_stats:
                hours[int(hour)] = count
            
            result['metrics']['hourly_activity'] = {
                'hours': hours,
                'peak_hour': hours.index(max(hours)),
                'total': sum(hours)
            }
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(f"自定义统计错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500

@statistics_bp.route('/export', methods=['GET', 'POST'])
@token_required
def export_statistics():
    """
    导出统计数据报表
    
    参数:
        token: 认证令牌
        start_date: 开始日期(YYYY-MM-DD)
        end_date: 结束日期(YYYY-MM-DD)
        format: 导出格式(csv, json, excel)
        type: 报表类型(daily, project, summary)
        project_code: 项目代码过滤（可选）
        
    返回:
        文件下载链接
    """
    # 从request中获取当前用户ID
    current_user_id = request.user_id
    
    try:
        # 获取请求参数
        start_date_str = request.args.get('start_date') or request.form.get('start_date')
        end_date_str = request.args.get('end_date') or request.form.get('end_date')
        export_format = request.args.get('format') or request.form.get('format', 'excel')
        report_type = request.args.get('type') or request.form.get('type', 'summary')
        project_code = request.args.get('project_code') or request.form.get('project_code')
        
        if not start_date_str or not end_date_str:
            return jsonify({
                'status': 'error',
                'message': '请提供开始和结束日期'
            }), 400
        
        # 验证格式
        if export_format not in ['csv', 'json', 'excel']:
            return jsonify({
                'status': 'error',
                'message': '不支持的导出格式'
            }), 400
        
        # 验证报表类型
        if report_type not in ['daily', 'project', 'summary']:
            return jsonify({
                'status': 'error',
                'message': '不支持的报表类型'
            }), 400
        
        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        
        # 检查日期范围
        date_range = (end_date - start_date).days
        if date_range < 0:
            return jsonify({
                'status': 'error',
                'message': '结束日期必须大于等于开始日期'
            }), 400
        
        if date_range > 90:
            return jsonify({
                'status': 'error',
                'message': '日期范围不能超过90天'
            }), 400
        
        # 根据报表类型生成数据
        data = []
        
        if report_type == 'daily':
            # 按天统计
            daily_stats = []
            current_date = start_date
            
            while current_date <= end_date:
                next_day = current_date + timedelta(days=1)
                
                # 查询当天数据
                query = PhoneRequest.query.filter(
                    PhoneRequest.user_id == current_user_id,
                    PhoneRequest.created_at.between(current_date, next_day - timedelta(seconds=1))
                )
                
                if project_code:
                    project = Project.query.filter_by(code=project_code).first()
                    if project:
                        query = query.filter(PhoneRequest.project_id == project.id)
                
                # 统计数据
                total_requests = query.count()
                successful_requests = query.filter(PhoneRequest.status.in_(['used', 'completed'])).count()
                
                # 计算成功率
                success_rate = 0
                if total_requests > 0:
                    success_rate = (successful_requests / total_requests) * 100
                
                # 计算消费
                cost = db.session.query(func.sum(Transaction.amount)).filter(
                    Transaction.user_id == current_user_id,
                    Transaction.type == 'consume',
                    Transaction.created_at.between(current_date, next_day - timedelta(seconds=1))
                ).scalar() or 0
                
                daily_stats.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'success_rate': round(success_rate, 2),
                    'cost': abs(cost)
                })
                
                current_date = next_day
            
            data = daily_stats
            
        elif report_type == 'project':
            # 按项目统计
            project_stats = db.session.query(
                Project.id, Project.name, Project.code, func.count(PhoneRequest.id)
            ).join(
                PhoneRequest, Project.id == PhoneRequest.project_id
            ).filter(
                PhoneRequest.user_id == current_user_id,
                PhoneRequest.created_at.between(start_date, end_date)
            ).group_by(
                Project.id
            ).all()
            
            for project_id, name, code, count in project_stats:
                # 计算成功率
                successful = PhoneRequest.query.filter(
                    PhoneRequest.user_id == current_user_id,
                    PhoneRequest.project_id == project_id,
                    PhoneRequest.status.in_(['used', 'completed']),
                    PhoneRequest.created_at.between(start_date, end_date)
                ).count()
                
                success_rate = 0
                if count > 0:
                    success_rate = (successful / count) * 100
                
                # 计算平均响应时间
                avg_time = db.session.query(
                    func.avg(func.extract('epoch', SMS.received_at - PhoneRequest.created_at))
                ).join(
                    PhoneRequest, SMS.phone_request_id == PhoneRequest.id
                ).filter(
                    PhoneRequest.user_id == current_user_id,
                    PhoneRequest.project_id == project_id,
                    PhoneRequest.created_at.between(start_date, end_date)
                ).scalar() or 0
                
                data.append({
                    'project_name': name,
                    'project_code': code,
                    'total_requests': count,
                    'successful_requests': successful,
                    'success_rate': round(success_rate, 2),
                    'avg_response_time': round(avg_time, 2)
                })
            
        else:  # summary
            # 汇总统计
            # 总请求数
            total_requests = PhoneRequest.query.filter(
                PhoneRequest.user_id == current_user_id,
                PhoneRequest.created_at.between(start_date, end_date)
            )
            
            if project_code:
                project = Project.query.filter_by(code=project_code).first()
                if project:
                    total_requests = total_requests.filter(PhoneRequest.project_id == project.id)
            
            request_count = total_requests.count()
            
            # 成功请求数
            successful_count = total_requests.filter(
                PhoneRequest.status.in_(['used', 'completed'])
            ).count()
            
            # 成功率
            success_rate = 0
            if request_count > 0:
                success_rate = (successful_count / request_count) * 100
            
            # 总消费
            total_cost = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user_id,
                Transaction.type == 'consume',
                Transaction.created_at.between(start_date, end_date)
            ).scalar() or 0
            
            # 使用的项目数
            project_count = db.session.query(func.count(func.distinct(PhoneRequest.project_id))).filter(
                PhoneRequest.user_id == current_user_id,
                PhoneRequest.created_at.between(start_date, end_date)
            ).scalar() or 0
            
            # 每日平均请求数
            daily_avg = request_count / (date_range + 1) if date_range > 0 else request_count
            
            data = [{
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d'),
                'total_days': date_range + 1,
                'total_requests': request_count,
                'successful_requests': successful_count,
                'success_rate': round(success_rate, 2),
                'total_cost': abs(total_cost),
                'daily_average_requests': round(daily_avg, 2),
                'project_count': project_count
            }]
        
        # 生成文件名
        filename = f"statistics_{report_type}_{start_date_str}_to_{end_date_str}"
        
        # 根据格式导出
        if export_format == 'json':
            # 导出为JSON
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            response = make_response(json_data)
            response.headers['Content-Disposition'] = f'attachment; filename={filename}.json'
            response.headers['Content-Type'] = 'application/json'
            return response
            
        elif export_format == 'csv':
            # 导出为CSV
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': '没有数据可导出'
                }), 404
                
            # 创建CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            response = make_response(output.getvalue())
            response.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'
            response.headers['Content-Type'] = 'text/csv'
            return response
            
        else:  # excel
            # 导出为Excel
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': '没有数据可导出'
                }), 404
                
            # 创建Excel
            df = pd.DataFrame(data)
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=report_type.capitalize())
                
                # 调整列宽
                worksheet = writer.sheets[report_type.capitalize()]
                for i, col in enumerate(df.columns):
                    max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.column_dimensions[get_column_letter(i + 1)].width = max_len
            
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Disposition'] = f'attachment; filename={filename}.xlsx'
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            return response
            
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(f"导出统计数据错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500 