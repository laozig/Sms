import requests
import json
import time
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:5000/api"

# 测试令牌 - 请替换为有效的令牌
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0"

def print_separator(title):
    """打印分隔线和标题"""
    print("\n" + "="*50)
    print(f"测试: {title}")
    print("="*50)

def print_response(response):
    """打印响应内容"""
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

def get_token():
    """获取有效的认证令牌"""
    login_url = f"{BASE_URL}/auth/login"
    login_params = {
        "username": "test_user",
        "password": "password123"
    }
    
    print_separator("登录获取令牌")
    print(f"请求URL: {login_url}")
    print(f"请求参数: {login_params}")
    
    try:
        response = requests.get(login_url, params=login_params)
        success, result = print_response(response)
        if success and 'token' in result:
            return result['token']
        else:
            print("无法获取有效令牌，将使用预设令牌。")
            return TEST_TOKEN
    except Exception as e:
        print(f"登录请求异常: {str(e)}")
        print("将使用预设令牌继续测试。")
        return TEST_TOKEN

# 基础API测试

def test_register():
    """测试注册API"""
    print_separator("注册 API")
    
    timestamp = int(time.time())
    url = f"{BASE_URL}/auth/register"
    params = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "password123"
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.post(url, json=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试注册API时发生异常: {str(e)}")
        return False

def test_get_profile(token):
    """测试获取个人资料API"""
    print_separator("获取个人资料 API")
    
    url = f"{BASE_URL}/auth/profile"
    params = {"token": token}
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试获取个人资料API时发生异常: {str(e)}")
        return False

def test_get_projects(token):
    """测试获取项目列表API"""
    print_separator("获取项目列表 API")
    
    url = f"{BASE_URL}/projects"
    params = {
        "token": token,
        "page": 1,
        "per_page": 5
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, result = print_response(response)
        if success and 'items' in result:
            return result.get('items', [])
        return []
    except Exception as e:
        print(f"测试获取项目列表API时发生异常: {str(e)}")
        return []

def test_get_balance(token):
    """测试查询余额API"""
    print_separator("查询余额 API")
    
    url = f"{BASE_URL}/account/balance"
    params = {"token": token}
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试查询余额API时发生异常: {str(e)}")
        return False

def test_get_number(token, project_code):
    """测试取号API"""
    print_separator("取号 API")
    
    if not project_code:
        print("没有可用的项目代码，跳过测试")
        return None
    
    url = f"{BASE_URL}/numbers/get"
    params = {
        "token": token,
        "project_code": project_code
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, result = print_response(response)
        if success and 'phone_number' in result:
            return result.get('phone_number', {}).get('request_id')
        return None
    except Exception as e:
        print(f"测试取号API时发生异常: {str(e)}")
        return None

# 新增API测试

def test_batch_get_numbers(token, project_code):
    """测试批量取号API"""
    print_separator("批量取号 API")
    
    if not project_code:
        print("没有可用的项目代码，跳过测试")
        return []
    
    url = f"{BASE_URL}/numbers/batch-get"
    params = {
        "token": token,
        "project_code": project_code,
        "count": 2
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, result = print_response(response)
        if success and result and 'phone_numbers' in result:
            # 保存请求ID用于后续测试
            request_ids = [phone.get('request_id') for phone in result.get('phone_numbers', [])]
            return request_ids
        return []
    except Exception as e:
        print(f"测试批量取号API时发生异常: {str(e)}")
        return []

def test_batch_release_numbers(token, request_ids):
    """测试批量释放号码API"""
    print_separator("批量释放号码 API")
    
    if not request_ids:
        print("没有可用的请求ID，跳过测试")
        return False
    
    url = f"{BASE_URL}/numbers/batch-release"
    params = {
        "token": token,
        "request_ids": ",".join(request_ids)
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试批量释放号码API时发生异常: {str(e)}")
        return False

def test_project_detail(token, project_id):
    """测试查询项目详情API"""
    print_separator("查询项目详情 API")
    
    if not project_id:
        print("没有可用的项目ID，跳过测试")
        return False
    
    url = f"{BASE_URL}/projects/{project_id}"
    params = {"token": token}
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试查询项目详情API时发生异常: {str(e)}")
        return False

def test_export_numbers(token):
    """测试导出号码记录API"""
    print_separator("导出号码记录 API")
    
    # 计算日期范围 (过去30天)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    url = f"{BASE_URL}/numbers/export"
    params = {
        "token": token,
        "format": "json",
        "start_date": start_date,
        "end_date": end_date
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试导出号码记录API时发生异常: {str(e)}")
        return False

def test_statistics(token):
    """测试获取统计数据API"""
    print_separator("获取统计数据 API")
    
    # 计算日期范围 (过去30天)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    url = f"{BASE_URL}/statistics"
    params = {
        "token": token,
        "type": "monthly",
        "start_date": start_date,
        "end_date": end_date
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试获取统计数据API时发生异常: {str(e)}")
        return False

def test_update_profile(token):
    """测试修改个人资料API"""
    print_separator("修改个人资料 API")
    
    url = f"{BASE_URL}/auth/update-profile"
    params = {
        "token": token,
        "email": f"test_{int(time.time())}@example.com"
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试修改个人资料API时发生异常: {str(e)}")
        return False

def test_create_order(token):
    """测试创建充值订单API"""
    print_separator("创建充值订单 API")
    
    url = f"{BASE_URL}/account/create-order"
    params = {
        "token": token,
        "amount": 100,
        "payment_method": "alipay"
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, result = print_response(response)
        if success and result and 'order' in result:
            return result.get('order', {}).get('order_id')
        return None
    except Exception as e:
        print(f"测试创建充值订单API时发生异常: {str(e)}")
        return None

def test_order_status(token, order_id):
    """测试查询充值订单状态API"""
    print_separator("查询充值订单状态 API")
    
    if not order_id:
        print("没有可用的订单ID，跳过测试")
        return False
    
    url = f"{BASE_URL}/account/order-status/{order_id}"
    params = {"token": token}
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试查询充值订单状态API时发生异常: {str(e)}")
        return False

def test_api_key(token):
    """测试设置API密钥API"""
    print_separator("设置API密钥 API")
    
    url = f"{BASE_URL}/auth/api-key"
    params = {
        "token": token,
        "action": "generate"
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试设置API密钥API时发生异常: {str(e)}")
        return False

def test_logout(token):
    """测试注销/刷新令牌API"""
    print_separator("注销/刷新令牌 API")
    
    url = f"{BASE_URL}/auth/logout"
    params = {"token": token}
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        success, _ = print_response(response)
        return success
    except Exception as e:
        print(f"测试注销/刷新令牌API时发生异常: {str(e)}")
        return False

def run_all_tests():
    """运行所有API测试"""
    print("\n====== 接码平台API测试 ======\n")
    
    results = {
        "success": 0,
        "failed": 0,
        "total": 0,
        "skipped": 0
    }
    
    # 测试服务器是否运行
    try:
        print("检查服务器是否运行...")
        requests.get(f"{BASE_URL}/auth/login", timeout=2)
        print("服务器已经运行")
    except:
        print("服务器未运行，请先启动服务器")
        return
    
    # 获取认证令牌
    token = get_token()
    
    # 基础API测试
    
    # 注册测试
    results["total"] += 1
    if test_register():
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 获取个人资料
    results["total"] += 1
    if test_get_profile(token):
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 获取余额
    results["total"] += 1
    if test_get_balance(token):
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 获取项目列表
    projects = test_get_projects(token)
    results["total"] += 1
    if projects:
        results["success"] += 1
        project_code = projects[0].get("code") if projects else None
        project_id = projects[0].get("id") if projects else None
    else:
        results["failed"] += 1
        project_code = None
        project_id = None
    
    # 取号测试
    results["total"] += 1
    request_id = test_get_number(token, project_code)
    if request_id:
        results["success"] += 1
    else:
        if not project_code:
            results["skipped"] += 1
        else:
            results["failed"] += 1
    
    # 新增API测试
    
    # 批量取号测试
    results["total"] += 1
    request_ids = test_batch_get_numbers(token, project_code)
    if request_ids:
        results["success"] += 1
    else:
        if not project_code:
            results["skipped"] += 1
        else:
            results["failed"] += 1
    
    # 批量释放号码测试
    results["total"] += 1
    if test_batch_release_numbers(token, request_ids):
        results["success"] += 1
    else:
        if not request_ids:
            results["skipped"] += 1
        else:
            results["failed"] += 1
    
    # 查询项目详情测试
    results["total"] += 1
    if test_project_detail(token, project_id):
        results["success"] += 1
    else:
        if not project_id:
            results["skipped"] += 1
        else:
            results["failed"] += 1
    
    # 导出号码记录测试
    results["total"] += 1
    if test_export_numbers(token):
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 获取统计数据测试
    results["total"] += 1
    if test_statistics(token):
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 修改个人资料测试
    results["total"] += 1
    if test_update_profile(token):
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 创建订单测试
    results["total"] += 1
    order_id = test_create_order(token)
    if order_id:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 查询订单状态测试
    results["total"] += 1
    if test_order_status(token, order_id):
        results["success"] += 1
    else:
        if not order_id:
            results["skipped"] += 1
        else:
            results["failed"] += 1
    
    # API密钥测试
    results["total"] += 1
    if test_api_key(token):
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 最后测试注销
    results["total"] += 1
    if test_logout(token):
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 打印测试结果汇总
    print("\n====== 测试结果汇总 ======")
    print(f"总测试数: {results['total']}")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    print(f"跳过: {results['skipped']}")
    print(f"成功率: {(results['success'] / (results['total'] - results['skipped'])) * 100:.2f}%")

if __name__ == "__main__":
    run_all_tests() 