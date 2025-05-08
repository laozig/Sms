# 接码平台后端

这是一个接码平台的Python后端系统，提供短信验证码接收服务。所有API均支持GET请求方式，方便直接在浏览器中访问和测试。

## 功能特性

- 用户注册与登录
- 修改密码和个人资料
- 查询账户余额和消费明细
- 搜索项目
- 收藏项目和取消收藏
- 查询专属对接项目
- 加入专属对接
- 取号（随机获取手机号）
- 指定取号（获取指定手机号）
- 释放号码
- 拉黑号码
- 获取短信验证码

## 系统要求

- Python 3.7+
- pip (Python包管理器)
- 虚拟环境(推荐使用venv或conda)

## 安装步骤

1. 克隆项目代码（或下载项目压缩包并解压）

```bash
git clone <仓库地址>
cd sms-platform-backend
```

2. 创建并激活虚拟环境

```bash
# 使用venv
python -m venv venv
# Windows上激活
venv\Scripts\activate
# Linux/Mac上激活
source venv/bin/activate
```

3. 安装依赖包

```bash
pip install -r requirements.txt
```

4. 配置环境变量（可选）

```bash
# Windows
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=True

# Linux/Mac
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=True
```

## 运行应用

```bash
# 方法1: 使用flask命令
flask run --host=0.0.0.0

# 方法2: 直接运行app.py
python app.py
```

默认情况下，应用将在 http://127.0.0.1:5000 上运行，可以通过局域网IP访问（如 http://192.168.x.x:5000）。

## 初始化数据库

应用首次启动时会自动创建所需的数据库表，无需手动创建。如果需要重置数据库：

```bash
# 进入Python交互式环境
python

# 在Python环境中执行
from app import create_app
from app.models import db

app = create_app()
with app.app_context():
    db.drop_all()  # 删除所有表
    db.create_all()  # 重新创建所有表
```

## API接口文档 (使用GET方法)

### 认证方式

系统支持以下方式传递认证令牌：

#### URL参数认证（推荐方式）
对于所有请求，直接在URL中通过`token`参数传递令牌：
```
/api/auth/profile?token=<JWT令牌>
```

这种方式简单直观，可以直接在浏览器地址栏中输入进行测试。

#### 请求体认证（备选方式）
如果使用POST请求，也可以在请求体中通过`token`字段传递令牌：
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "other_param": "value"
}
```

### 认证相关

#### 1. 用户注册
- **URL**: `/api/auth/register`
- **方法**: GET
- **参数**:
  - `username`: 用户名
  - `email`: 邮箱地址
  - `password`: 密码
- **示例**: `/api/auth/register?username=test&email=test@example.com&password=123456`
- **响应**:
  ```json
  {
    "message": "注册成功",
    "token": "JWT令牌",
    "user": {
      "id": 1,
      "username": "test",
      "email": "test@example.com",
      "balance": 0.0,
      "is_admin": false,
      "is_active": true,
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00"
    }
  }
  ```

#### 2. 用户登录
- **URL**: `/api/auth/login`
- **方法**: GET
- **参数**:
  - `username`: 用户名
  - `password`: 密码
- **示例**: `/api/auth/login?username=test&password=123456`
- **响应**:
  ```json
  {
    "message": "登录成功",
    "token": "JWT令牌",
    "user": {
      "id": 1,
      "username": "test",
      "email": "test@example.com",
      "balance": 100.0,
      "is_admin": false,
      "is_active": true,
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00"
    }
  }
  ```

#### 3. 修改密码
- **URL**: `/api/auth/change-password`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `old_password`: 旧密码
  - `new_password`: 新密码
- **示例**: `/api/auth/change-password?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&old_password=123456&new_password=654321`
- **响应**:
  ```json
  {
    "message": "密码修改成功"
  }
  ```

#### 4. 获取个人资料
- **URL**: `/api/auth/profile`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
- **示例**: `/api/auth/profile?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA`
- **响应**:
  ```json
  {
    "id": 1,
    "username": "test",
    "email": "test@example.com",
    "balance": 100.0,
    "is_admin": false,
    "is_active": true,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
  ```

### 项目相关

#### 1. 获取项目列表
- **URL**: `/api/projects`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `page`: 页码（默认1）
  - `per_page`: 每页数量（默认10）
  - `keyword`: 搜索关键词（可选）
- **示例**: `/api/projects?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&page=1&per_page=20&keyword=微信`
- **响应**:
  ```json
  {
    "items": [
      {
        "id": 1,
        "name": "微信登录",
        "code": "wechat_login",
        "description": "微信验证码登录",
        "price": 1.0,
        "success_rate": 0.98,
        "available": true,
        "is_exclusive": false,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
  ```

#### 2. 搜索项目
- **URL**: `/api/projects/search`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `keyword`: 搜索关键词（必需）
- **示例**: `/api/projects/search?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&keyword=微信`
- **响应**:
  ```json
  [
    {
      "id": 1,
      "name": "微信登录",
      "code": "wechat_login",
      "description": "微信验证码登录",
      "price": 1.0,
      "success_rate": 0.98,
      "available": true,
      "is_exclusive": false
    }
  ]
  ```

#### 3. 收藏项目
- **URL**: `/api/projects/favorite/{project_id}`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
- **示例**: `/api/projects/favorite/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA`
- **响应**:
  ```json
  {
    "message": "项目收藏成功"
  }
  ```

#### 4. 取消收藏项目
- **URL**: `/api/projects/favorite/{project_id}`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `action`: 取值必须为"delete"
- **示例**: `/api/projects/favorite/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&action=delete`
- **响应**:
  ```json
  {
    "message": "取消收藏成功"
  }
  ```

#### 5. 获取收藏的项目列表
- **URL**: `/api/projects/favorites`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `page`: 页码（默认1）
  - `per_page`: 每页数量（默认10）
- **示例**: `/api/projects/favorites?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&page=1&per_page=20`
- **响应**: 与获取项目列表相同

#### 6. 获取专属对接的项目列表
- **URL**: `/api/projects/exclusive`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `page`: 页码（默认1）
  - `per_page`: 每页数量（默认10）
- **示例**: `/api/projects/exclusive?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&page=1&per_page=20`
- **响应**: 与获取项目列表相同

#### 7. 加入专属对接
- **URL**: `/api/projects/exclusive/{project_id}`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
- **示例**: `/api/projects/exclusive/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA`
- **响应**:
  ```json
  {
    "message": "加入专属对接成功"
  }
  ```

#### 8. 获取所有可加入的专属项目
- **URL**: `/api/projects/all-exclusive`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `page`: 页码（默认1）
  - `per_page`: 每页数量（默认10）
- **示例**: `/api/projects/all-exclusive?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&page=1&per_page=20`
- **响应**: 与获取项目列表相同

### 号码相关

#### 1. 取号（获取手机号）
- **URL**: `/api/numbers/get`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `project_code`: 项目代码
- **示例**: `/api/numbers/get?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&project_code=wechat_login`
- **响应**:
  ```json
  {
    "message": "获取号码成功",
    "phone_number": {
      "id": 1,
      "number": "13800138000",
      "status": "available",
      "project_id": 1,
      "project_name": "微信登录",
      "user_id": 1,
      "sms_code": null,
      "request_id": "req_12345",
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00",
      "released_at": null
    }
  }
  ```

#### 2. 指定取号（获取指定手机号）
- **URL**: `/api/numbers/get-specific`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `project_code`: 项目代码
  - `number`: 手机号码
- **示例**: `/api/numbers/get-specific?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&project_code=wechat_login&number=13800138000`
- **响应**: 与取号接口相同

#### 3. 获取短信验证码
- **URL**: `/api/numbers/sms/{request_id}`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
- **示例**: `/api/numbers/sms/req_12345?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA`
- **响应**:
  ```json
  {
    "message": "获取验证码成功",
    "code": "123456",
    "phone_number": {
      "id": 1,
      "number": "13800138000",
      "status": "used",
      "project_id": 1,
      "project_name": "微信登录",
      "user_id": 1,
      "sms_code": "123456",
      "request_id": "req_12345",
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00",
      "released_at": null
    }
  }
  ```

#### 4. 释放号码
- **URL**: `/api/numbers/release/{request_id}`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
- **示例**: `/api/numbers/release/req_12345?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA`
- **响应**:
  ```json
  {
    "message": "号码释放成功"
  }
  ```

#### 5. 拉黑号码
- **URL**: `/api/numbers/blacklist`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `number`: 手机号码
  - `reason`: 拉黑原因（可选）
- **示例**: `/api/numbers/blacklist?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&number=13800138000&reason=诈骗号码`
- **响应**:
  ```json
  {
    "message": "号码已加入黑名单"
  }
  ```

#### 6. 获取我的号码列表
- **URL**: `/api/numbers/my-numbers`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `page`: 页码（默认1）
  - `per_page`: 每页数量（默认10）
  - `status`: 状态过滤（可选：available, used, released, blacklisted）
- **示例**: `/api/numbers/my-numbers?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&page=1&per_page=20&status=available`
- **响应**:
  ```json
  {
    "items": [
      {
        "id": 1,
        "number": "13800138000",
        "status": "available",
        "project_id": 1,
        "project_name": "微信登录",
        "user_id": 1,
        "sms_code": null,
        "request_id": "req_12345",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
        "released_at": null
      }
    ],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
  ```

### 账户相关

#### 1. 查询余额
- **URL**: `/api/account/balance`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
- **示例**: `/api/account/balance?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA`
- **响应**:
  ```json
  {
    "balance": 100.0
  }
  ```

#### 2. 获取交易记录
- **URL**: `/api/account/transactions`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌
  - `page`: 页码（默认1）
  - `per_page`: 每页数量（默认10）
  - `type`: 交易类型过滤（可选：topup, consume, refund）
- **示例**: `/api/account/transactions?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&page=1&per_page=20&type=consume`
- **响应**:
  ```json
  {
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "amount": -1.0,
        "balance": 99.0,
        "type": "consume",
        "description": "获取项目微信登录的手机号码",
        "reference_id": "req_12345",
        "created_at": "2023-01-01T00:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
  ```

#### 3. 账户充值
- **URL**: `/api/account/topup`
- **方法**: GET
- **参数**:
  - `token`: JWT令牌（登录后获取）
  - `amount`: 充值金额
  - `payment_method`: 支付方式（如：alipay, wechat）
- **示例**: `/api/account/topup?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&amount=100&payment_method=alipay`
- **响应**:
  ```json
  {
    "message": "充值成功",
    "balance": 200.0
  }
  ```

## 使用实例

### 基本流程示例

下面是一个完整的使用流程示例：

1. **注册用户**
   ```
   GET http://localhost:5000/api/auth/register?username=test&email=test@example.com&password=123456
   ```

2. **登录**
   ```
   GET http://localhost:5000/api/auth/login?username=test&password=123456
   ```
   *记录返回的令牌(token)，用于后续请求*

3. **查询余额**
   ```
   GET http://localhost:5000/api/account/balance?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA
   ```

4. **充值账户**
   ```
   GET http://localhost:5000/api/account/topup?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&amount=100&payment_method=alipay
   ```

5. **查看项目列表**
   ```
   GET http://localhost:5000/api/projects?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA
   ```

6. **收藏项目**
   ```
   GET http://localhost:5000/api/projects/favorite/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA
   ```

7. **获取手机号**
   ```
   GET http://localhost:5000/api/numbers/get?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&project_code=wechat_login
   ```

8. **获取短信验证码**
   ```
   GET http://localhost:5000/api/numbers/sms/req_12345?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA
   ```
   *req_12345为上一步返回的request_id*

9. **释放号码**
   ```
   GET http://localhost:5000/api/numbers/release/req_12345?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA
   ```

### 如何在浏览器中快速测试

在浏览器中可以使用以下步骤快速测试API：

1. 首先登录获取令牌:
   ```
   http://localhost:5000/api/auth/login?username=test&password=123456
   ```

2. 复制返回结果中的令牌(token)值

3. 直接在浏览器地址栏中访问其他API，添加token参数:
   ```
   http://localhost:5000/api/account/balance?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA
   ```

4. 对于需要多个参数的API，使用&连接参数:
   ```
   http://localhost:5000/api/projects/search?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6InRlc3QiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTc0NjcwMTIzMX0.l1M_dt9dUWtCyqxuf5gDTVcTy5XGmNHqBBCfwIwwnPA&keyword=微信
   ```

这种方式使得API测试非常简单直观，无需使用任何工具，直接在浏览器中输入URL即可。

## 常见问题解答

1. **如何获取专属对接的项目？**
   
   首先使用 `/api/projects/all-exclusive` 接口查看所有可加入的专属项目，然后使用 `/api/projects/exclusive/{project_id}` 接口加入专属对接，加入后即可使用该项目的号码。

2. **如何查看我已经收藏的项目？**
   
   使用 `/api/projects/favorites` 接口可以查看您已收藏的项目列表。

3. **如何查看消费明细？**
   
   使用 `/api/account/transactions` 接口，可以查看所有交易记录，包括充值和消费明细。

4. **如何拉黑一个号码？**
   
   使用 `/api/numbers/blacklist?number=手机号&reason=原因` 接口。

5. **如何取号和获取验证码？**
   
   首先使用 `/api/numbers/get?project_code=项目代码` 或 `/api/numbers/get-specific?project_code=项目代码&number=手机号` 接口获取手机号，然后使用返回的 `request_id` 调用 `/api/numbers/sms/{request_id}` 接口获取验证码。

## 浏览器使用提示

当使用浏览器直接访问API时，可能会遇到以下问题：

1. **跨域问题**：如果前端和后端不在同一域名下运行，可能会遇到跨域问题。后端已经配置了CORS，应该可以正常工作。

2. **授权问题**：大多数API需要JWT令牌。浏览器测试时可以：
   - 使用Chrome的ModHeader扩展添加Authorization头
   - 使用Postman等API测试工具
   - 编写一个简单的HTML页面，使用JavaScript添加Authorization头

3. **GET请求参数安全性**：使用GET方法时，参数会显示在URL中，包括敏感信息如密码。在生产环境中，敏感操作应考虑使用POST方法。

## 二次开发指南

### 项目结构

```
sms-platform-backend/
├── app/                    # 应用目录
│   ├── __init__.py         # 应用初始化
│   ├── config.py           # 配置文件
│   ├── models.py           # 数据库模型
│   ├── utils.py            # 工具函数
│   ├── routes/             # 路由目录
│   │   ├── auth.py         # 认证相关路由
│   │   ├── projects.py     # 项目相关路由
│   │   ├── numbers.py      # 号码相关路由
│   │   └── account.py      # 账户相关路由
│   ├── static/             # 静态文件目录
│   └── templates/          # 模板目录
├── app.py                  # 应用入口
├── requirements.txt        # 依赖列表
└── README.md               # 项目说明
```

### 添加新功能

1. 在相应的模型文件中添加新的数据库模型
2. 在相应的路由文件中添加新的API端点
3. 更新API文档

### 集成其他接码平台

要集成其他接码平台，您需要修改 `app/utils.py` 中的 `SMSApiClient` 类，实现相应平台的API调用。 