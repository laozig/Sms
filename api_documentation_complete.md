# 接码平台API文档

## 目录
- [通用说明](#通用说明)
- [用户认证](#用户认证)
- [项目管理](#项目管理)
- [号码管理](#号码管理)
- [账户管理](#账户管理)
- [统计数据](#统计数据)
- [状态码说明](#状态码说明)
- [注意事项](#注意事项)

## 通用说明

所有API支持GET和POST请求方法，认证令牌可通过以下方式提供：
1. URL参数: `?token=您的令牌`
2. POST请求体JSON: `{"token": "您的令牌"}`
3. 请求头: `Authorization: Bearer 您的令牌`（优先级最低）

## 用户认证

### 注册
```
GET/POST /api/auth/register
```

**参数**:
- `username`: 用户名
- `email`: 邮箱
- `password`: 密码

**返回**: 
- `token`: 认证令牌

**示例**:
```
GET http://localhost:5000/api/auth/register?username=test_user&email=test@example.com&password=password123
```

### 登录
```
GET/POST /api/auth/login
```

**参数**:
- `username`: 用户名
- `password`: 密码

**返回**:
- `token`: 认证令牌

**示例**:
```
GET http://localhost:5000/api/auth/login?username=test_user&password=password123
```

### 获取个人资料
```
GET/POST /api/auth/profile
```

**参数**:
- `token`: 认证令牌

**返回**:
- 用户信息

**示例**:
```
GET http://localhost:5000/api/auth/profile?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

### 修改个人资料
```
GET/POST /api/auth/update-profile
```

**参数**:
- `token`: 认证令牌
- `email`: 新邮箱（可选）
- `password`: 新密码（可选）
- `avatar`: 头像URL（可选）

**返回**:
- 更新后的用户信息

**示例**:
```
GET http://localhost:5000/api/auth/update-profile?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&email=new_email@example.com
```

### 修改密码
```
GET/POST /api/auth/change-password
```

**参数**:
- `token`: 认证令牌
- `old_password`: 旧密码
- `new_password`: 新密码

**返回**:
- 操作结果

**示例**:
```
GET http://localhost:5000/api/auth/change-password?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&old_password=password123&new_password=newpassword123
```

### 注销/刷新令牌
```
GET/POST /api/auth/logout
```

**参数**:
- `token`: 认证令牌

**返回**:
- 操作结果

**示例**:
```
GET http://localhost:5000/api/auth/logout?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

### 设置API密钥
```
GET/POST /api/auth/api-key
```

**参数**:
- `token`: 认证令牌
- `action`: 操作类型(generate, revoke)

**返回**:
- API密钥信息

**示例**:
```
GET http://localhost:5000/api/auth/api-key?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&action=generate
```

## 项目管理

### 获取项目列表
```
GET/POST /api/projects
```

**参数**:
- `token`: 认证令牌
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10）
- `keyword`: 搜索关键词（可选）

**返回**:
- 项目列表分页数据

**示例**:
```
GET http://localhost:5000/api/projects?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&page=1&per_page=10
```

### 查询项目详情
```
GET/POST /api/projects/{project_id}
```

**参数**:
- `token`: 认证令牌
- `project_id`: 项目ID

**返回**:
- 项目详细信息
- 相关统计数据

**示例**:
```
GET http://localhost:5000/api/projects/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

### 搜索项目
```
GET/POST /api/projects/search
```

**参数**:
- `token`: 认证令牌
- `keyword`: 搜索关键词

**返回**:
- 符合条件的项目列表

**示例**:
```
GET http://localhost:5000/api/projects/search?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&keyword=微信
```

### 收藏/取消收藏项目
```
GET/POST /api/projects/favorite/{project_id}
```

**参数**:
- `token`: 认证令牌
- `action`: 动作（可选，默认为添加收藏，值为"delete"表示取消收藏）

**返回**:
- 操作结果

**示例**:
```
# 收藏项目ID为2的项目
GET http://localhost:5000/api/projects/favorite/2?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0

# 取消收藏项目ID为1的项目
GET http://localhost:5000/api/projects/favorite/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&action=delete
```

### 获取收藏的项目列表
```
GET/POST /api/projects/favorites
```

**参数**:
- `token`: 认证令牌
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10）

**返回**:
- 收藏的项目列表分页数据

**示例**:
```
GET http://localhost:5000/api/projects/favorites?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&page=1&per_page=10
```

### 获取专属对接的项目列表
```
GET/POST /api/projects/exclusive
```

**参数**:
- `token`: 认证令牌
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10）

**返回**:
- 专属对接的项目列表分页数据

**示例**:
```
GET http://localhost:5000/api/projects/exclusive?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&page=1&per_page=10
```

### 获取所有可加入的专属项目
```
GET/POST /api/projects/all-exclusive
```

**参数**:
- `token`: 认证令牌
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10）

**返回**:
- 所有可加入的专属项目列表分页数据

**示例**:
```
GET http://localhost:5000/api/projects/all-exclusive?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&page=1&per_page=10
```

### 加入专属对接
```
GET/POST /api/projects/exclusive/{project_id}
```

**参数**:
- `token`: 认证令牌

**返回**:
- 操作结果

**示例**:
```
GET http://localhost:5000/api/projects/exclusive/3?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

## 号码管理

### 取号
```
GET/POST /api/numbers/get
```

**参数**:
- `token`: 认证令牌
- `project_code`: 项目代码

**返回**:
- 手机号信息
- 获取短信链接

**示例**:
```
GET http://localhost:5000/api/numbers/get?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&project_code=wechat_login
```

### 批量取号
```
GET/POST /api/numbers/batch-get
```

**参数**:
- `token`: 认证令牌
- `project_code`: 项目代码
- `count`: 需要获取的号码数量(1-10)

**返回**:
- 多个手机号信息列表
- 批量操作相关链接

**示例**:
```
GET http://localhost:5000/api/numbers/batch-get?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&project_code=wechat_login&count=3
```

### 获取短信
```
GET/POST /api/numbers/sms/{request_id}
```

**参数**:
- `token`: 认证令牌
- `request_id`: 取号请求ID

**返回**:
- 短信验证码信息

**示例**:
```
GET http://localhost:5000/api/numbers/sms/req_12345abc?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

### 提交短信
```
GET/POST /api/numbers/sms-submit/{request_id}
```

**参数**:
- `token`: 认证令牌
- `request_id`: 取号请求ID
- `sms_code`: 短信验证码

**返回**:
- 操作结果

**示例**:
```
GET http://localhost:5000/api/numbers/sms-submit/req_12345abc?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&sms_code=123456
```

### 释放号码
```
GET/POST /api/numbers/release/{request_id}
```

**参数**:
- `token`: 认证令牌
- `request_id`: 取号请求ID

**返回**:
- 操作结果

**示例**:
```
GET http://localhost:5000/api/numbers/release/req_12345abc?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

### 批量释放号码
```
GET/POST /api/numbers/batch-release
```

**参数**:
- `token`: 认证令牌
- `request_ids`: 请求ID列表，用逗号分隔

**返回**:
- 操作结果

**示例**:
```
GET http://localhost:5000/api/numbers/batch-release?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&request_ids=req_12345abc,req_67890def
```

### 获取号码列表
```
GET/POST /api/numbers/list
```

**参数**:
- `token`: 认证令牌
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10）
- `status`: 状态过滤（可选）
- `project_code`: 项目代码过滤（可选）

**返回**:
- 号码列表分页数据

**示例**:
```
GET http://localhost:5000/api/numbers/list?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&page=1&per_page=10
```

### 导出号码记录
```
GET/POST /api/numbers/export
```

**参数**:
- `token`: 认证令牌
- `format`: 导出格式(csv, json, excel)
- `start_date`: 开始日期(YYYY-MM-DD)
- `end_date`: 结束日期(YYYY-MM-DD)
- `status`: 状态过滤（可选）

**返回**:
- 文件下载链接

**示例**:
```
GET http://localhost:5000/api/numbers/export?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&format=csv&start_date=2025-01-01&end_date=2025-05-01
```

### 加入黑名单
```
GET/POST /api/numbers/blacklist/add
```

**参数**:
- `token`: 认证令牌
- `number`: 手机号码

**返回**:
- 操作结果

**示例**:
```
GET http://localhost:5000/api/numbers/blacklist/add?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&number=13800138000
```

### 查询黑名单列表
```
GET/POST /api/numbers/blacklist
```

**参数**:
- `token`: 认证令牌
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10）

**返回**:
- 黑名单列表分页数据

**示例**:
```
GET http://localhost:5000/api/numbers/blacklist?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&page=1&per_page=10
```

### 移除黑名单
```
GET/POST /api/numbers/blacklist/remove/{blacklist_id}
```

**参数**:
- `token`: 认证令牌
- `blacklist_id`: 黑名单ID

**返回**:
- 操作结果

**示例**:
```
GET http://localhost:5000/api/numbers/blacklist/remove/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

## 账户管理

### 查询余额
```
GET/POST /api/account/balance
```

**参数**:
- `token`: 认证令牌

**返回**:
- `balance`: 账户余额

**示例**:
```
GET http://localhost:5000/api/account/balance?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

### 创建充值订单
```
GET/POST /api/account/create-order
```

**参数**:
- `token`: 认证令牌
- `amount`: 充值金额
- `payment_method`: 支付方式（如：alipay, wechat, card）
- `coupon_code`: 优惠券代码（可选）

**返回**:
- 订单信息和支付链接

**示例**:
```
GET http://localhost:5000/api/account/create-order?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&amount=100&payment_method=alipay
```

### 查询充值订单状态
```
GET/POST /api/account/order-status/{order_id}
```

**参数**:
- `token`: 认证令牌
- `order_id`: 订单ID

**返回**:
- 订单状态信息

**示例**:
```
GET http://localhost:5000/api/account/order-status/order_12345abc?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0
```

### 查询交易记录
```
GET/POST /api/account/transactions
```

**参数**:
- `token`: 认证令牌
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10）
- `start_date`: 开始日期(YYYY-MM-DD)（可选）
- `end_date`: 结束日期(YYYY-MM-DD)（可选）
- `type`: 交易类型过滤（可选）

**返回**:
- 交易记录列表分页数据

**示例**:
```
GET http://localhost:5000/api/account/transactions?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&page=1&per_page=10
```

## 统计数据

### 获取统计数据
```
GET/POST /api/statistics
```

**参数**:
- `token`: 认证令牌
- `type`: 统计类型(daily, weekly, monthly)
- `start_date`: 开始日期(YYYY-MM-DD)
- `end_date`: 结束日期(YYYY-MM-DD)

**返回**:
- 统计数据

**示例**:
```
GET http://localhost:5000/api/statistics?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InRlc3RfdXNlciIsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzQ2NzAzMjc5fQ.DxE43OzVAmN1H9moiTLNvhiNCSwRzaKTeEMUHRvIEH0&type=monthly&start_date=2025-01-01&end_date=2025-05-01
```

## 状态码说明

- 200: 请求成功
- 201: 创建成功
- 400: 请求参数错误
- 401: 认证失败
- 403: 权限不足
- 404: 资源不存在
- 429: 请求过于频繁
- 500: 服务器内部错误

## 注意事项

1. 所有API都有频率限制，请勿频繁请求
2. 取号后需要在15分钟内获取验证码，否则号码将自动释放
3. 所有时间默认使用UTC时间，特别注明的除外
4. 余额不足时，取号将失败
5. API密钥应妥善保管，请勿泄露 