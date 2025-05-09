# 接码平台管理员API文档

本文档详细说明了接码平台管理员API的使用方法，包括接口地址、参数、返回值等信息。

## 认证

所有管理员API都需要通过`token`参数进行认证，并且该token必须属于具有管理员权限的用户。

认证方式：
- URL参数：`?token=YOUR_TOKEN`
- 请求头：`Authorization: Bearer YOUR_TOKEN`

## 用户管理

### 获取用户列表

```
GET /api/admin/users
```

**参数：**
- `page`: 页码，默认1
- `per_page`: 每页数量，默认20，最大100
- `keyword`: 搜索关键词，可选

**返回：**
```json
{
  "items": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "password": "admin123",
      "balance": 1000.0,
      "is_admin": true,
      "is_active": true,
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 1,
  "pages": 1,
  "page": 1,
  "per_page": 20
}
```

### 获取用户详情

```
GET /api/admin/users/{user_id}
```

**返回：**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "balance": 1000.0,
    "is_admin": true,
    "is_active": true,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
}
```

### 创建用户

```
POST /api/admin/users
```

**请求体：**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "is_admin": false
}
```

**返回：**
```json
{
  "message": "用户创建成功",
  "user": {
    "id": 2,
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123",
    "balance": 0.0,
    "is_admin": false,
    "is_active": true,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
}
```

### 更新用户

```
PUT /api/admin/users/{user_id}
```

**请求体：**
```json
{
  "username": "updateduser",
  "email": "updated@example.com",
  "password": "newpassword",
  "is_admin": false,
  "is_active": true
}
```

**返回：**
```json
{
  "message": "用户信息已更新",
  "user": {
    "id": 2,
    "username": "updateduser",
    "email": "updated@example.com",
    "password": "newpassword",
    "balance": 0.0,
    "is_admin": false,
    "is_active": true,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
}
```

### 禁用用户

```
DELETE /api/admin/users/{user_id}
```

**返回：**
```json
{
  "message": "用户已禁用"
}
```

## 项目管理

### 获取项目列表

```
GET /api/admin/projects
```

**参数：**
- `page`: 页码，默认1
- `per_page`: 每页数量，默认20，最大100
- `keyword`: 搜索关键词，可选

**返回：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "测试项目",
      "code": "test",
      "description": "这是一个测试项目",
      "price": 1.0,
      "success_rate": 0.95,
      "available": true,
      "is_exclusive": false,
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 1,
  "pages": 1,
  "page": 1,
  "per_page": 20
}
```

### 创建项目

```
POST /api/admin/projects
```

**请求体：**
```json
{
  "name": "新项目",
  "code": "newproject",
  "price": 2.0,
  "description": "这是一个新项目",
  "success_rate": 0.8,
  "available": true,
  "is_exclusive": false
}
```

**返回：**
```json
{
  "message": "项目创建成功",
  "project": {
    "id": 2,
    "name": "新项目",
    "code": "newproject",
    "description": "这是一个新项目",
    "price": 2.0,
    "success_rate": 0.8,
    "available": true,
    "is_exclusive": false,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
}
```

### 更新项目

```
PUT /api/admin/projects/{project_id}
```

**请求体：**
```json
{
  "name": "更新项目",
  "code": "updatedproject",
  "price": 3.0,
  "description": "这是一个更新后的项目",
  "success_rate": 0.9,
  "available": true,
  "is_exclusive": true
}
```

**返回：**
```json
{
  "message": "项目信息已更新",
  "project": {
    "id": 2,
    "name": "更新项目",
    "code": "updatedproject",
    "description": "这是一个更新后的项目",
    "price": 3.0,
    "success_rate": 0.9,
    "available": true,
    "is_exclusive": true,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
}
```

### 删除项目

```
DELETE /api/admin/projects/{project_id}
```

**返回：**
```json
{
  "message": "项目已删除"
}
```

## 号码管理

### 获取号码列表

```
GET /api/admin/numbers
```

**参数：**
- `page`: 页码，默认1
- `per_page`: 每页数量，默认20，最大100
- `keyword`: 搜索关键词，可选
- `status`: 号码状态，可选

**返回：**
```json
{
  "items": [
    {
      "id": 1,
      "number": "13800138000",
      "status": "available",
      "project_id": 1,
      "project_name": "测试项目",
      "user_id": 1,
      "sms_code": null,
      "request_id": "req123",
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00",
      "released_at": null
    }
  ],
  "total": 1,
  "pages": 1,
  "page": 1,
  "per_page": 20
}
```

### 更新号码

```
PUT /api/admin/numbers/{number_id}
```

**请求体：**
```json
{
  "status": "blacklisted"
}
```

**返回：**
```json
{
  "message": "号码信息已更新",
  "number": {
    "id": 1,
    "number": "13800138000",
    "status": "blacklisted",
    "project_id": 1,
    "project_name": "测试项目",
    "user_id": 1,
    "sms_code": null,
    "request_id": "req123",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00",
    "released_at": null
  }
}
```

### 删除号码

```
DELETE /api/admin/numbers/{number_id}
```

**返回：**
```json
{
  "message": "号码已删除"
}
```

## 通知管理

### 获取通知列表

```
GET /api/admin/notifications
```

**参数：**
- `page`: 页码，默认1
- `per_page`: 每页数量，默认20，最大100

**返回：**
```json
{
  "items": [
    {
      "id": 1,
      "title": "系统通知",
      "content": "系统将于明日凌晨2点进行维护",
      "type": "info",
      "is_read": false,
      "is_global": true,
      "user_id": null,
      "created_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 1,
  "pages": 1,
  "page": 1,
  "per_page": 20
}
```

### 创建通知

```
POST /api/admin/notifications
```

**请求体：**
```json
{
  "title": "新通知",
  "content": "这是一条新通知",
  "type": "warning",
  "is_global": true,
  "user_id": null
}
```

**返回：**
```json
{
  "message": "通知创建成功",
  "notification_id": 2
}
```

### 更新通知

```
PUT /api/admin/notifications/{notification_id}
```

**请求体：**
```json
{
  "title": "更新通知",
  "content": "这是一条更新后的通知",
  "type": "success",
  "is_global": false
}
```

**返回：**
```json
{
  "message": "通知已更新"
}
```

### 删除通知

```
DELETE /api/admin/notifications/{notification_id}
```

**返回：**
```json
{
  "message": "通知已删除"
}
```

## 统计管理

### 获取全局统计数据

```
GET /api/admin/statistics
```

**返回：**
```json
{
  "user_count": 10,
  "project_count": 5,
  "number_count": 100,
  "transaction_count": 50,
  "total_balance": 5000.0,
  "total_income": 10000.0,
  "total_consume": 5000.0
}
``` 