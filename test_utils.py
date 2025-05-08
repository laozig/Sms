import requests
import json
import time
from datetime import datetime, timedelta

class APITester:
    """API测试工具类"""
    
    def __init__(self, base_url="http://localhost:5000/api", test_token=None):
        """
        初始化API测试工具
        
        参数:
            base_url (str): API基础URL
            test_token (str, optional): 测试令牌
        """
        self.base_url = base_url
        self.test_token = test_token
        self.session = requests.Session()
    
    def print_separator(self, title):
        """打印分隔线和标题"""
        print("\n" + "="*50)
        print(f"测试: {title}")
        print("="*50)
    
    def print_response(self, response):
        """
        打印响应内容
        
        参数:
            response (Response): 请求响应对象
            
        返回:
            tuple: (成功标志, 响应数据)
        """
        try:
            print(f"状态码: {response.status_code}")
            if response.status_code == 200 or response.status_code == 201:
                try:
                    result = response.json()
                    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    return True, result
                except ValueError:
                    print(f"响应不是有效的JSON: {response.text}")
                    return False, None
            else:
                print(f"请求失败: {response.text}")
                return False, None
        except Exception as e:
            print(f"处理响应时发生错误: {str(e)}")
            return False, None
    
    def get_token(self, username="test_user", password="password123"):
        """
        获取有效的认证令牌
        
        参数:
            username (str): 用户名
            password (str): 密码
            
        返回:
            str: 认证令牌
        """
        login_url = f"{self.base_url}/auth/login"
        login_params = {
            "username": username,
            "password": password
        }
        
        self.print_separator("登录获取令牌")
        print(f"请求URL: {login_url}")
        print(f"请求参数: {login_params}")
        
        try:
            response = requests.get(login_url, params=login_params)
            success, result = self.print_response(response)
            if success and 'token' in result:
                return result['token']
            else:
                print("无法获取有效令牌，将使用预设令牌。")
                return self.test_token
        except Exception as e:
            print(f"登录请求异常: {str(e)}")
            print("将使用预设令牌继续测试。")
            return self.test_token
    
    def test_api(self, method, endpoint, params=None, data=None, json_data=None, 
                token=None, title=None, expected_status_codes=(200, 201)):
        """
        通用API测试方法
        
        参数:
            method (str): 请求方法 ('GET', 'POST', 等)
            endpoint (str): API端点路径
            params (dict, optional): URL参数
            data (dict, optional): 表单数据
            json_data (dict, optional): JSON数据
            token (str, optional): 认证令牌
            title (str, optional): 测试标题
            expected_status_codes (tuple, optional): 预期的成功状态码
            
        返回:
            tuple: (成功标志, 响应数据)
        """
        if token:
            # 将令牌添加到参数中
            if params is None:
                params = {}
            params['token'] = token
        
        url = f"{self.base_url}/{endpoint}"
        if title:
            self.print_separator(title)
        
        print(f"请求URL: {url}")
        print(f"请求方法: {method}")
        if params:
            print(f"请求参数: {params}")
        if data:
            print(f"表单数据: {data}")
        if json_data:
            print(f"JSON数据: {json_data}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data
            )
            success, result = self.print_response(response)
            
            # 检查状态码是否符合预期
            if response.status_code in expected_status_codes:
                return True, result
            return False, result
            
        except Exception as e:
            print(f"请求异常: {str(e)}")
            return False, None

# 测试工具函数
def generate_test_data():
    """生成测试数据"""
    timestamp = int(time.time())
    return {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "password123"
    }

def calculate_date_range(days=30):
    """
    计算日期范围
    
    参数:
        days (int): 日期范围天数
        
    返回:
        tuple: (开始日期, 结束日期)
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return start_date, end_date

def format_request_ids(request_ids):
    """
    格式化请求ID列表为字符串
    
    参数:
        request_ids (list): 请求ID列表
        
    返回:
        str: 逗号分隔的请求ID字符串
    """
    if not request_ids:
        return ""
    return ",".join(request_ids) 