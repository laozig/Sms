import jwt
import requests
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

# 设置日志
logger = logging.getLogger(__name__)


def generate_token(user_id, username, is_admin=False, expires_delta=None):
    """
    生成JWT令牌
    
    参数:
        user_id (int): 用户ID
        username (str): 用户名
        is_admin (bool): 是否为管理员
        expires_delta (timedelta, optional): 过期时间增量
        
    返回:
        str: JWT令牌
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=1)
        
    exp = datetime.utcnow() + expires_delta
    
    payload = {
        'user_id': user_id,
        'username': username,
        'is_admin': is_admin,
        'exp': exp
    }
    
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token


def api_error_handler(func):
    """
    API错误处理装饰器
    
    捕获并统一处理API函数中的异常
    
    用法:
        @api_error_handler
        def api_function():
            # 实现API逻辑
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return jsonify({'message': '认证令牌已过期'}), 401
        except jwt.InvalidTokenError:
            logger.warning("无效的令牌")
            return jsonify({'message': '无效的认证令牌'}), 401
        except ValueError as e:
            logger.error(f"参数错误: {str(e)}")
            return jsonify({'message': f'参数错误: {str(e)}'}), 400
        except Exception as e:
            logger.exception(f"API处理异常: {str(e)}")
            return jsonify({'message': '服务器内部错误', 'error': str(e)}), 500
    return wrapper


def token_required(f):
    """
    JWT令牌验证装饰器
    
    用法:
        @token_required
        def protected_route():
            # 只有验证通过的请求才会到达这里
            pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. 尝试从GET请求参数中获取令牌（优先级最高）
        if request.args and 'token' in request.args:
            token = request.args.get('token')
            logger.debug(f"从GET参数中获取到令牌: {token[:10]}...")
        
        # 2. 尝试从POST请求体中获取令牌（优先级第二）
        if not token and request.method == 'POST':
            # 2.1 从JSON请求体获取
            if request.is_json:
                # 首先检查token字段
                if 'token' in request.json:
                    token = request.json.get('token')
                    logger.debug(f"从JSON请求体中获取到令牌: {token[:10]}...")
                # 然后检查Authorization字段
                elif 'Authorization' in request.json:
                    auth_value = request.json.get('Authorization')
                    if auth_value and auth_value.startswith('Bearer '):
                        token = auth_value.split(' ')[1]
                    else:
                        token = auth_value  # 假设整个值就是令牌
                    logger.debug(f"从JSON请求体的Authorization字段获取到令牌: {token[:10]}...")
            # 2.2 从表单数据获取
            elif request.form:
                if 'token' in request.form:
                    token = request.form.get('token')
                    logger.debug(f"从表单数据中获取到令牌: {token[:10]}...")
                elif 'Authorization' in request.form:
                    auth_value = request.form.get('Authorization')
                    if auth_value and auth_value.startswith('Bearer '):
                        token = auth_value.split(' ')[1]
                    else:
                        token = auth_value  # 假设整个值就是令牌
                    logger.debug(f"从表单数据的Authorization字段获取到令牌: {token[:10]}...")
        
        # 3. 最后尝试从请求头中获取令牌（优先级最低）
        if not token and 'Authorization' in request.headers:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = auth_header  # 假设整个值就是令牌
            logger.debug(f"从请求头中获取到令牌: {token[:10]}...")
        
        if not token:
            return jsonify({
                'message': '缺少认证令牌',
                'help': '请在URL中通过token参数提供令牌，例如：?token=您的令牌'
            }), 401
        
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # 将用户信息添加到请求上下文
            request.user_id = payload['user_id']
            request.username = payload['username']
            request.is_admin = payload['is_admin']
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '认证令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '无效的认证令牌'}), 401
            
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    管理员权限验证装饰器
    
    用法:
        @token_required
        @admin_required
        def admin_route():
            # 只有管理员才能访问
            pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'is_admin') or not request.is_admin:
            return jsonify({'message': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    
    return decorated


class SMSApiClient:
    """接码平台API客户端"""
    
    def __init__(self, base_url=None, api_key=None):
        """
        初始化API客户端
        
        参数:
            base_url (str, optional): API基础URL
            api_key (str, optional): API密钥
        """
        self.base_url = base_url or current_app.config['SMS_API_BASE_URL']
        self.api_key = api_key or current_app.config['SMS_API_KEY']
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        # 禁用代理设置
        self.session.proxies = {
            'http': None,
            'https': None
        }
        
        # 使用模拟API进行本地测试
        self.use_mock = current_app.config.get('USE_MOCK_API', True)
        if self.use_mock:
            # 导入模拟API
            try:
                from .mock_api import mock_api
                self.mock_api = mock_api
                logger.info("使用模拟API进行测试")
            except ImportError:
                logger.warning("未找到模拟API模块，将使用真实API")
                self.use_mock = False
    
    def _handle_response(self, response):
        """处理API响应"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {e}")
            try:
                error_data = response.json()
                logger.error(f"API错误: {error_data}")
                return error_data
            except ValueError:
                logger.error(f"API响应不是有效的JSON: {response.text}")
                return {'success': False, 'message': '无法解析API响应', 'status_code': response.status_code}
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return {'success': False, 'message': f'请求异常: {str(e)}'}
        except ValueError as e:
            logger.error(f"JSON解析错误: {e}, 响应内容: {response.text}")
            return {'success': False, 'message': '无法解析API响应'}
    
    def get_projects(self):
        """获取所有可用项目"""
        if self.use_mock:
            return self.mock_api.get_projects()
            
        url = f"{self.base_url}/projects"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def search_projects(self, keyword):
        """搜索项目"""
        if self.use_mock:
            return self.mock_api.search_projects(keyword)
            
        url = f"{self.base_url}/projects/search"
        params = {'keyword': keyword}
        response = self.session.get(url, params=params)
        return self._handle_response(response)
    
    def get_phone_number(self, project_code):
        """获取手机号码"""
        if self.use_mock:
            return self.mock_api.get_phone_number(project_code)
            
        url = f"{self.base_url}/numbers"
        data = {'project_code': project_code}
        response = self.session.post(url, json=data)
        return self._handle_response(response)
    
    def get_specific_phone_number(self, project_code, number):
        """获取指定手机号码"""
        if self.use_mock:
            return self.mock_api.get_specific_phone_number(project_code, number)
            
        url = f"{self.base_url}/numbers/specific"
        data = {
            'project_code': project_code,
            'number': number
        }
        response = self.session.post(url, json=data)
        return self._handle_response(response)
    
    def release_phone_number(self, request_id):
        """释放手机号码"""
        if self.use_mock:
            return self.mock_api.release_phone_number(request_id)
            
        url = f"{self.base_url}/numbers/{request_id}/release"
        response = self.session.post(url)
        return self._handle_response(response)
    
    def blacklist_phone_number(self, number, reason=None):
        """拉黑手机号码"""
        if self.use_mock:
            return self.mock_api.blacklist_phone_number(number, reason)
            
        url = f"{self.base_url}/numbers/blacklist"
        data = {
            'number': number,
            'reason': reason
        }
        response = self.session.post(url, json=data)
        return self._handle_response(response)
    
    def get_sms_code(self, request_id):
        """获取短信验证码"""
        if self.use_mock:
            return self.mock_api.get_sms_code(request_id)
            
        url = f"{self.base_url}/sms/{request_id}"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def check_balance(self):
        """查询账户余额"""
        if self.use_mock:
            return self.mock_api.check_balance()
            
        url = f"{self.base_url}/account/balance"
        response = self.session.get(url)
        return self._handle_response(response)


def calculate_price(project, count=1):
    """
    计算项目价格
    
    参数:
        project (Project): 项目对象
        count (int): 数量
        
    返回:
        float: 总价
    """
    return project.price * count


def validate_pagination_params(page, per_page, max_per_page=100):
    """
    验证分页参数
    
    参数:
        page (int): 页码
        per_page (int): 每页数量
        max_per_page (int): 每页最大数量
        
    返回:
        tuple: (页码, 每页数量)
    """
    try:
        page = int(page) if page is not None else 1
        per_page = int(per_page) if per_page is not None else current_app.config.get('ITEMS_PER_PAGE', 10)
    except (TypeError, ValueError):
        page = 1
        per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    
    # 确保page至少为1
    page = max(1, page)
    
    # 确保per_page在合理范围内
    per_page = max(1, min(per_page, max_per_page))
    
    return page, per_page 