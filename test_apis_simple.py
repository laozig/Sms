from test_utils import APITester, generate_test_data, calculate_date_range, format_request_ids
import requests

# API测试令牌
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0"

def run_all_tests():
    """运行所有API测试"""
    print("\n====== 接码平台API测试 (简化版) ======\n")
    
    results = {
        "success": 0,
        "failed": 0,
        "total": 0,
        "skipped": 0
    }
    
    # 初始化测试工具
    tester = APITester(test_token=TEST_TOKEN)
    
    # 测试服务器是否运行
    try:
        print("检查服务器是否运行...")
        requests.get(f"{tester.base_url}/auth/login", timeout=2)
        print("服务器已经运行")
    except:
        print("服务器未运行，请先启动服务器")
        return
    
    # 获取认证令牌
    token = tester.get_token()
    
    # 1. 测试注册API
    results["total"] += 1
    test_data = generate_test_data()
    success, _ = tester.test_api(
        method="POST",
        endpoint="auth/register",
        json_data=test_data,
        title="注册 API",
        expected_status_codes=(200, 201)
    )
    if success:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 2. 测试获取个人资料API
    results["total"] += 1
    success, _ = tester.test_api(
        method="GET",
        endpoint="auth/profile",
        token=token,
        title="获取个人资料 API"
    )
    if success:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 3. 测试查询余额API
    results["total"] += 1
    success, _ = tester.test_api(
        method="GET",
        endpoint="account/balance",
        token=token,
        title="查询余额 API"
    )
    if success:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 4. 测试获取项目列表API
    results["total"] += 1
    success, result = tester.test_api(
        method="GET",
        endpoint="projects",
        params={"page": 1, "per_page": 5},
        token=token,
        title="获取项目列表 API"
    )
    
    if success and 'items' in result and result['items']:
        results["success"] += 1
        project_code = result['items'][0].get("code")
        project_id = result['items'][0].get("id")
    else:
        results["failed"] += 1
        project_code = None
        project_id = None
    
    # 5. 测试取号API
    results["total"] += 1
    if project_code:
        success, result = tester.test_api(
            method="GET",
            endpoint="numbers/get",
            params={"project_code": project_code},
            token=token,
            title="取号 API"
        )
        if success and 'phone_number' in result:
            results["success"] += 1
            request_id = result['phone_number'].get('request_id')
        else:
            results["failed"] += 1
            request_id = None
    else:
        print("没有可用的项目代码，跳过取号测试")
        results["skipped"] += 1
        request_id = None
    
    # 6. 测试批量取号API
    results["total"] += 1
    if project_code:
        success, result = tester.test_api(
            method="GET",
            endpoint="numbers/batch-get",
            params={"project_code": project_code, "count": 2},
            token=token,
            title="批量取号 API"
        )
        if success and 'phone_numbers' in result:
            results["success"] += 1
            request_ids = [phone.get('request_id') for phone in result['phone_numbers']]
        else:
            results["failed"] += 1
            request_ids = []
    else:
        print("没有可用的项目代码，跳过批量取号测试")
        results["skipped"] += 1
        request_ids = []
    
    # 7. 测试批量释放号码API
    results["total"] += 1
    if request_ids:
        success, _ = tester.test_api(
            method="GET",
            endpoint="numbers/batch-release",
            params={"request_ids": format_request_ids(request_ids)},
            token=token,
            title="批量释放号码 API"
        )
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
    else:
        print("没有可用的请求ID，跳过批量释放测试")
        results["skipped"] += 1
    
    # 8. 测试查询项目详情API
    results["total"] += 1
    if project_id:
        success, _ = tester.test_api(
            method="GET",
            endpoint=f"projects/{project_id}",
            token=token,
            title="查询项目详情 API"
        )
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
    else:
        print("没有可用的项目ID，跳过查询项目详情测试")
        results["skipped"] += 1
    
    # 9. 测试导出号码记录API
    results["total"] += 1
    start_date, end_date = calculate_date_range(30)
    success, _ = tester.test_api(
        method="GET",
        endpoint="numbers/export",
        params={"format": "json", "start_date": start_date, "end_date": end_date},
        token=token,
        title="导出号码记录 API"
    )
    if success:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 10. 测试获取统计数据API
    results["total"] += 1
    success, _ = tester.test_api(
        method="GET",
        endpoint="statistics",
        params={"type": "monthly", "start_date": start_date, "end_date": end_date},
        token=token,
        title="获取统计数据 API"
    )
    if success:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 11. 测试修改个人资料API
    results["total"] += 1
    email = generate_test_data()["email"]
    success, _ = tester.test_api(
        method="GET",
        endpoint="auth/update-profile",
        params={"email": email},
        token=token,
        title="修改个人资料 API"
    )
    if success:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 12. 测试创建充值订单API
    results["total"] += 1
    success, result = tester.test_api(
        method="GET",
        endpoint="account/create-order",
        params={"amount": 100, "payment_method": "alipay"},
        token=token,
        title="创建充值订单 API"
    )
    if success and 'order' in result:
        results["success"] += 1
        order_id = result['order'].get('order_id')
    else:
        results["failed"] += 1
        order_id = None
    
    # 13. 测试查询充值订单状态API
    results["total"] += 1
    if order_id:
        success, _ = tester.test_api(
            method="GET",
            endpoint=f"account/order-status/{order_id}",
            token=token,
            title="查询充值订单状态 API"
        )
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
    else:
        print("没有可用的订单ID，跳过查询订单状态测试")
        results["skipped"] += 1
    
    # 14. 测试设置API密钥API
    results["total"] += 1
    success, _ = tester.test_api(
        method="GET",
        endpoint="auth/api-key",
        params={"action": "generate"},
        token=token,
        title="设置API密钥 API"
    )
    if success:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 15. 测试注销/刷新令牌API
    results["total"] += 1
    success, _ = tester.test_api(
        method="GET",
        endpoint="auth/logout",
        token=token,
        title="注销/刷新令牌 API"
    )
    if success:
        results["success"] += 1
    else:
        results["failed"] += 1
    
    # 打印测试结果汇总
    print("\n====== 测试结果汇总 ======")
    print(f"总测试数: {results['total']}")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    print(f"跳过: {results['skipped']}")
    
    # 计算成功率（排除跳过的测试）
    if results['total'] - results['skipped'] > 0:
        success_rate = (results['success'] / (results['total'] - results['skipped'])) * 100
        print(f"成功率: {success_rate:.2f}%")
    else:
        print("成功率: N/A (没有执行任何测试)")

if __name__ == "__main__":
    run_all_tests() 