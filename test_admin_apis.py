import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# 获取管理员token
def get_admin_token():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    else:
        print(f"获取管理员token失败: {response.text}")
        return None

# 测试所有管理员API
def test_admin_apis():
    # 获取管理员token
    token = get_admin_token()
    if not token:
        print("无法获取管理员token，测试终止")
        return False
    
    print("\n===== 开始测试管理员API =====\n")
    
    # 测试用户管理API
    test_user_apis(token)
    
    # 测试项目管理API
    test_project_apis(token)
    
    # 测试号码管理API
    test_number_apis(token)
    
    # 测试通知管理API
    test_notification_apis(token)
    
    # 测试统计API
    test_statistics_api(token)
    
    print("\n===== 管理员API测试完成 =====\n")
    return True

# 测试用户管理API
def test_user_apis(token):
    print("\n----- 测试用户管理API -----\n")
    
    # 获取用户列表
    print("测试: 获取用户列表")
    response = requests.get(f"{BASE_URL}/admin/users?token={token}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户总数: {data.get('total')}")
    else:
        print(f"错误: {response.text}")
    
    # 创建新用户
    print("\n测试: 创建新用户")
    new_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "password123",
        "is_admin": False
    }
    response = requests.post(
        f"{BASE_URL}/admin/users?token={token}",
        json=new_user
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        user_data = response.json().get("user")
        user_id = user_data.get("id")
        print(f"新用户ID: {user_id}")
        
        # 获取用户详情
        print("\n测试: 获取用户详情")
        response = requests.get(f"{BASE_URL}/admin/users/{user_id}?token={token}")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"用户详情: {response.json().get('user').get('username')}")
        
        # 更新用户
        print("\n测试: 更新用户")
        update_data = {
            "username": f"updated_{new_user['username']}",
            "email": f"updated_{new_user['email']}"
        }
        response = requests.put(
            f"{BASE_URL}/admin/users/{user_id}?token={token}",
            json=update_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"更新后用户名: {response.json().get('user').get('username')}")
        
        # 禁用用户
        print("\n测试: 禁用用户")
        response = requests.delete(f"{BASE_URL}/admin/users/{user_id}?token={token}")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"结果: {response.json().get('message')}")
    else:
        print(f"创建用户失败: {response.text}")

# 测试项目管理API
def test_project_apis(token):
    print("\n----- 测试项目管理API -----\n")
    
    # 获取项目列表
    print("测试: 获取项目列表")
    response = requests.get(f"{BASE_URL}/admin/projects?token={token}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"项目总数: {data.get('total')}")
    else:
        print(f"错误: {response.text}")
    
    # 创建新项目
    print("\n测试: 创建新项目")
    new_project = {
        "name": f"测试项目_{int(time.time())}",
        "code": f"test_{int(time.time())}",
        "price": 1.5,
        "description": "这是一个测试项目",
        "success_rate": 0.85,
        "available": True,
        "is_exclusive": False
    }
    response = requests.post(
        f"{BASE_URL}/admin/projects?token={token}",
        json=new_project
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        project_data = response.json().get("project")
        project_id = project_data.get("id")
        print(f"新项目ID: {project_id}")
        
        # 更新项目
        print("\n测试: 更新项目")
        update_data = {
            "name": f"更新_{new_project['name']}",
            "price": 2.0,
            "success_rate": 0.9
        }
        response = requests.put(
            f"{BASE_URL}/admin/projects/{project_id}?token={token}",
            json=update_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"更新后项目名: {response.json().get('project').get('name')}")
        
        # 删除项目
        print("\n测试: 删除项目")
        response = requests.delete(f"{BASE_URL}/admin/projects/{project_id}?token={token}")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"结果: {response.json().get('message')}")
    else:
        print(f"创建项目失败: {response.text}")

# 测试号码管理API
def test_number_apis(token):
    print("\n----- 测试号码管理API -----\n")
    
    # 获取号码列表
    print("测试: 获取号码列表")
    response = requests.get(f"{BASE_URL}/admin/numbers?token={token}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"号码总数: {data.get('total')}")
        
        # 如果有号码，测试更新和删除
        if data.get('total') > 0:
            number_id = data.get('items')[0].get('id')
            
            # 更新号码
            print("\n测试: 更新号码")
            update_data = {
                "status": "blacklisted"
            }
            response = requests.put(
                f"{BASE_URL}/admin/numbers/{number_id}?token={token}",
                json=update_data
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"更新后号码状态: {response.json().get('number').get('status')}")
            
            # 删除号码
            print("\n测试: 删除号码")
            response = requests.delete(f"{BASE_URL}/admin/numbers/{number_id}?token={token}")
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"结果: {response.json().get('message')}")
        else:
            print("没有可用号码进行测试")
    else:
        print(f"错误: {response.text}")

# 测试通知管理API
def test_notification_apis(token):
    print("\n----- 测试通知管理API -----\n")
    
    # 获取通知列表
    print("测试: 获取通知列表")
    response = requests.get(f"{BASE_URL}/admin/notifications?token={token}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"通知总数: {data.get('total')}")
    else:
        print(f"错误: {response.text}")
    
    # 创建新通知
    print("\n测试: 创建新通知")
    new_notification = {
        "title": f"测试通知_{int(time.time())}",
        "content": "这是一条测试通知",
        "type": "info",
        "is_global": True
    }
    response = requests.post(
        f"{BASE_URL}/admin/notifications?token={token}",
        json=new_notification
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        notification_id = response.json().get("notification_id")
        print(f"新通知ID: {notification_id}")
        
        # 更新通知
        print("\n测试: 更新通知")
        update_data = {
            "title": f"更新_{new_notification['title']}",
            "content": "这是一条更新后的测试通知",
            "type": "warning"
        }
        response = requests.put(
            f"{BASE_URL}/admin/notifications/{notification_id}?token={token}",
            json=update_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"结果: {response.json().get('message')}")
        
        # 删除通知
        print("\n测试: 删除通知")
        response = requests.delete(f"{BASE_URL}/admin/notifications/{notification_id}?token={token}")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"结果: {response.json().get('message')}")
    else:
        print(f"创建通知失败: {response.text}")

# 测试统计API
def test_statistics_api(token):
    print("\n----- 测试统计API -----\n")
    
    # 获取全局统计数据
    print("测试: 获取全局统计数据")
    response = requests.get(f"{BASE_URL}/admin/statistics?token={token}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户数: {data.get('user_count')}")
        print(f"项目数: {data.get('project_count')}")
        print(f"号码数: {data.get('number_count')}")
        print(f"交易数: {data.get('transaction_count')}")
        print(f"总余额: {data.get('total_balance')}")
        print(f"总收入: {data.get('total_income')}")
        print(f"总消费: {data.get('total_consume')}")
    else:
        print(f"错误: {response.text}")

if __name__ == "__main__":
    test_admin_apis() 