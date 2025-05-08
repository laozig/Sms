import random
import string
import time
from datetime import datetime

class MockSMSApi:
    """模拟SMS API服务，用于本地测试"""
    
    def __init__(self):
        """初始化模拟服务"""
        self.projects = [
            {
                'id': 1,
                'name': '微信登录',
                'code': 'wechat_login',
                'description': '微信验证码登录',
                'price': 1.0,
                'success_rate': 0.98,
                'available': True,
                'is_exclusive': False
            },
            {
                'id': 2,
                'name': '支付宝登录',
                'code': 'alipay_login',
                'description': '支付宝验证码登录',
                'price': 1.2,
                'success_rate': 0.97,
                'available': True,
                'is_exclusive': False
            },
            {
                'id': 3,
                'name': '抖音登录',
                'code': 'douyin_login',
                'description': '抖音验证码登录',
                'price': 1.5,
                'success_rate': 0.95,
                'available': True,
                'is_exclusive': True
            }
        ]
        
        self.phone_numbers = {}  # request_id -> number_info
        self.blacklist = []      # 黑名单号码列表
    
    def get_projects(self):
        """获取所有可用项目"""
        return {'success': True, 'data': self.projects}
    
    def search_projects(self, keyword):
        """搜索项目"""
        results = [p for p in self.projects if keyword.lower() in p['name'].lower() or keyword.lower() in p['description'].lower()]
        return {'success': True, 'data': results}
    
    def get_phone_number(self, project_code):
        """获取手机号码"""
        # 查找项目
        project = next((p for p in self.projects if p['code'] == project_code), None)
        if not project:
            return {'success': False, 'message': f'未找到项目代码为 {project_code} 的项目'}
        
        # 生成随机手机号
        phone_number = '138' + ''.join(random.choices(string.digits, k=8))
        
        # 生成请求ID
        request_id = f'req_{int(time.time())}_{random.randint(1000, 9999)}'
        
        # 保存号码信息
        number_info = {
            'id': random.randint(1, 1000),
            'number': phone_number,
            'status': 'available',
            'project_id': project['id'],
            'project_name': project['name'],
            'user_id': 1,  # 假设用户ID
            'sms_code': None,
            'request_id': request_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'released_at': None
        }
        
        self.phone_numbers[request_id] = number_info
        
        return {
            'success': True,
            'message': '获取号码成功',
            'phone_number': number_info
        }
    
    def get_specific_phone_number(self, project_code, number):
        """获取指定手机号码"""
        # 查找项目
        project = next((p for p in self.projects if p['code'] == project_code), None)
        if not project:
            return {'success': False, 'message': f'未找到项目代码为 {project_code} 的项目'}
        
        # 检查号码是否在黑名单中
        if number in self.blacklist:
            return {'success': False, 'message': f'号码 {number} 已被拉黑'}
        
        # 生成请求ID
        request_id = f'req_{int(time.time())}_{random.randint(1000, 9999)}'
        
        # 保存号码信息
        number_info = {
            'id': random.randint(1, 1000),
            'number': number,
            'status': 'available',
            'project_id': project['id'],
            'project_name': project['name'],
            'user_id': 1,  # 假设用户ID
            'sms_code': None,
            'request_id': request_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'released_at': None
        }
        
        self.phone_numbers[request_id] = number_info
        
        return {
            'success': True,
            'message': '获取号码成功',
            'phone_number': number_info
        }
    
    def release_phone_number(self, request_id):
        """释放手机号码"""
        if request_id not in self.phone_numbers:
            return {'success': False, 'message': f'未找到请求ID为 {request_id} 的号码'}
        
        number_info = self.phone_numbers[request_id]
        number_info['status'] = 'released'
        number_info['released_at'] = datetime.now().isoformat()
        number_info['updated_at'] = datetime.now().isoformat()
        
        return {'success': True, 'message': '号码释放成功'}
    
    def blacklist_phone_number(self, number, reason=None):
        """拉黑手机号码"""
        if number in self.blacklist:
            return {'success': False, 'message': f'号码 {number} 已在黑名单中'}
        
        self.blacklist.append(number)
        
        # 更新任何使用该号码的请求
        for request_id, info in self.phone_numbers.items():
            if info['number'] == number:
                info['status'] = 'blacklisted'
                info['updated_at'] = datetime.now().isoformat()
        
        return {'success': True, 'message': '号码已加入黑名单'}
    
    def get_sms_code(self, request_id):
        """获取短信验证码"""
        if request_id not in self.phone_numbers:
            return {'success': False, 'message': f'未找到请求ID为 {request_id} 的号码'}
        
        number_info = self.phone_numbers[request_id]
        
        # 如果已经有验证码，直接返回
        if number_info['sms_code']:
            return {
                'success': True,
                'message': '获取验证码成功',
                'code': number_info['sms_code'],
                'phone_number': number_info
            }
        
        # 生成随机验证码
        sms_code = ''.join(random.choices(string.digits, k=6))
        
        # 更新号码信息
        number_info['sms_code'] = sms_code
        number_info['status'] = 'used'
        number_info['updated_at'] = datetime.now().isoformat()
        
        return {
            'success': True,
            'message': '获取验证码成功',
            'code': sms_code,
            'phone_number': number_info
        }
    
    def check_balance(self):
        """查询账户余额"""
        return {
            'success': True,
            'balance': random.uniform(50.0, 500.0)
        }

# 创建全局实例
mock_api = MockSMSApi() 