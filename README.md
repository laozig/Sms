# SMS接码平台后端

这是一个SMS接码平台的Python后端系统，提供短信验证码接收服务。系统采用Flask框架构建，使用RESTful API风格设计。

## 功能特性

- 用户注册与登录
- 修改密码和个人资料
- 查询账户余额和消费明细
- 搜索项目
- 获取手机号
- 释放号码
- 获取短信验证码
- 管理员功能
- 系统监控

## 系统架构

本项目采用MVC架构，具体结构如下：

- **Models**: 数据模型层，定义数据库表结构
- **Views**: 视图层，处理HTTP请求和响应
- **Controllers**: 控制器层，实现业务逻辑
- **Services**: 服务层，提供公共服务功能

## 系统要求

- Python 3.7+
- Flask 2.2+
- SQLAlchemy 2.0+
- JWT认证
- Redis(可选，用于缓存和异步任务)

## 安装步骤

1. 克隆项目代码

```bash
git clone <仓库地址>
cd sms-platform
```

2. 创建并激活虚拟环境

```bash
# 使用venv
python -m venv .venv
# Windows上激活
.venv\Scripts\activate
# Linux/Mac上激活
source .venv/bin/activate
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
# 直接运行app.py
python app.py
```

默认情况下，应用将在 http://localhost:5000 上运行。

## 初始化数据库

首次使用时，运行以下命令初始化数据库并创建测试数据：

```bash
python init_db.py
```

这将创建初始管理员账户和测试用户：
- 管理员: admin/admin123
- 测试用户: test/test123

## API接口文档

详细的API接口文档请参考 [API文档.md](API文档.md)。

### 认证方式

系统使用JWT进行认证，支持以下方式传递认证令牌：

1. **请求头认证**
   ```
   Authorization: Bearer <JWT令牌>
   ```

2. **URL参数认证**
   ```
   ?token=<JWT令牌>
   ```

3. **请求体认证**
   ```json
   {
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   }
   ```

## 项目优化

本项目实施了以下优化:

1. **代码结构优化**：
   - 采用MVC架构，创建了清晰的目录结构
   - 分离业务逻辑与路由处理
   - 应用单例模式管理数据库连接和缓存服务

2. **数据库优化**：
   - 实现数据库连接池，避免频繁创建销毁连接
   - 改进事务管理，确保数据一致性
   - 优化查询，添加适当索引

3. **性能优化**：
   - 添加缓存机制(内存与Redis缓存)
   - 实现多线程和异步处理耗时操作
   - 使用装饰器实现函数级缓存

4. **监控与日志**：
   - 创建全面的监控系统，收集API调用指标
   - 实现结构化日志记录
   - 添加性能测试脚本

5. **安全性改进**：
   - 基于JWT的认证机制
   - 改进输入验证和参数检查
   - 统一错误处理与响应格式

## 贡献指南

1. Fork 本仓库
2. 创建新分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 