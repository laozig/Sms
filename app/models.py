from datetime import datetime
import bcrypt
import random
import string
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 用户收藏项目关联表（已弃用，改用UserFavorite模型）
# user_favorite_projects = db.Table('user_favorite_projects',
#     db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
#     db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
#     db.Column('created_at', db.DateTime, default=datetime.utcnow)
# )

# 用户专属对接关联表（已弃用，改用UserExclusiveProject模型）
# user_exclusive_projects = db.Table('user_exclusive_projects',
#     db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
#     db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
#     db.Column('created_at', db.DateTime, default=datetime.utcnow)
# )

# 生成5位随机数字的项目ID
def generate_project_id():
    while True:
        # 生成5位随机数字
        project_id = random.randint(10000, 99999)
        # 检查是否已存在
        if not Project.query.filter_by(project_id=str(project_id)).first():
            return str(project_id)

# 生成8位随机小写字母的专属项目后缀
def generate_exclusive_suffix():
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(8))

class UserFavorite(db.Model):
    """用户收藏项目模型"""
    __tablename__ = 'user_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 设置联合唯一约束
    __table_args__ = (db.UniqueConstraint('user_id', 'project_id', name='uix_user_project_favorite'),)
    
    def to_dict(self):
        """将用户收藏对象转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat()
        }

class UserExclusiveProject(db.Model):
    """用户专属对接项目模型"""
    __tablename__ = 'user_exclusive_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 设置联合唯一约束
    __table_args__ = (db.UniqueConstraint('user_id', 'project_id', name='uix_user_project_exclusive'),)
    
    def to_dict(self):
        """将用户专属对接对象转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat()
        }

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # 明文密码
    balance = db.Column(db.Float, default=0.0)  # 用户余额，默认0
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    phone_numbers = db.relationship('PhoneNumber', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    # 更新关联关系为使用新模型
    favorites = db.relationship('UserFavorite', backref='user', lazy=True)
    exclusive_projects_relation = db.relationship('UserExclusiveProject', backref='user', lazy=True)
    
    # 通过属性提供与旧代码兼容的接口
    @property
    def favorite_projects(self):
        """获取收藏的项目列表"""
        from sqlalchemy.orm import joinedload
        favorites = db.session.query(UserFavorite).filter_by(user_id=self.id).options(
            joinedload(UserFavorite.project)
        ).all()
        return [f.project for f in favorites]
    
    @property
    def exclusive_projects(self):
        """获取专属对接的项目列表"""
        from sqlalchemy.orm import joinedload
        exclusives = db.session.query(UserExclusiveProject).filter_by(user_id=self.id).options(
            joinedload(UserExclusiveProject.project)
        ).all()
        return [e.project for e in exclusives]
    
    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.password = password  # 直接保存明文密码
        self.is_admin = is_admin
        self.balance = 0.0  # 确保余额初始为0
    
    def check_password(self, password):
        """验证密码"""
        return self.password == password  # 直接比较明文密码
    
    def to_dict(self):
        """将用户对象转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password': self.password,  # 添加明文密码到返回结果
            'balance': self.balance,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Project(db.Model):
    """项目模型（对应接码平台的项目/应用）"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(20), unique=True, nullable=False)  # 5位随机数字ID
    exclusive_id = db.Column(db.String(30), unique=True, nullable=True)  # 专属项目ID格式：project_id----xxxxxxxx
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)  # 项目代码
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)  # 单价
    success_rate = db.Column(db.Float, default=0.0)  # 成功率
    available = db.Column(db.Boolean, default=True)  # 是否可用
    is_exclusive = db.Column(db.Boolean, default=False)  # 是否为专属项目
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    phone_numbers = db.relationship('PhoneNumber', backref='project', lazy=True)
    user_favorites = db.relationship('UserFavorite', backref='project', lazy=True)
    user_exclusives = db.relationship('UserExclusiveProject', backref='project', lazy=True)
    
    def __init__(self, name, code, price, description=None, is_exclusive=False):
        self.name = name
        self.code = code
        self.price = price
        self.description = description
        self.is_exclusive = is_exclusive
        
        # 生成项目ID
        self.project_id = generate_project_id()
        
        # 如果是专属项目，生成专属ID
        if is_exclusive:
            self.exclusive_id = f"{self.project_id}----{generate_exclusive_suffix()}"
    
    # 当项目变为专属项目时，生成专属ID
    def set_exclusive(self, is_exclusive):
        self.is_exclusive = is_exclusive
        if is_exclusive and not self.exclusive_id:
            self.exclusive_id = f"{self.project_id}----{generate_exclusive_suffix()}"
        elif not is_exclusive:
            self.exclusive_id = None
    
    # 通过属性提供与旧代码兼容的接口
    @property
    def favorited_by(self):
        """获取收藏该项目的用户列表"""
        from sqlalchemy.orm import joinedload
        favorites = db.session.query(UserFavorite).filter_by(project_id=self.id).options(
            joinedload(UserFavorite.user)
        ).all()
        return [f.user for f in favorites]
    
    @property
    def exclusive_users(self):
        """获取加入该专属项目的用户列表"""
        from sqlalchemy.orm import joinedload
        exclusives = db.session.query(UserExclusiveProject).filter_by(project_id=self.id).options(
            joinedload(UserExclusiveProject.user)
        ).all()
        return [e.user for e in exclusives]
    
    def to_dict(self):
        """将项目对象转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'exclusive_id': self.exclusive_id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'price': self.price,
            'success_rate': self.success_rate,
            'available': self.available,
            'is_exclusive': self.is_exclusive,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class PhoneNumber(db.Model):
    """手机号码模型"""
    __tablename__ = 'phone_numbers'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, used, blacklisted, released
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sms_code = db.Column(db.String(20))  # 收到的短信验证码
    request_id = db.Column(db.String(100))  # 上游平台请求ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    released_at = db.Column(db.DateTime)  # 释放时间
    
    def to_dict(self):
        """将手机号码对象转换为字典"""
        return {
            'id': self.id,
            'number': self.number,
            'status': self.status,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'user_id': self.user_id,
            'sms_code': self.sms_code,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'released_at': self.released_at.isoformat() if self.released_at else None
        }

class BlacklistedNumber(db.Model):
    """黑名单号码模型"""
    __tablename__ = 'blacklisted_numbers'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """将黑名单号码对象转换为字典"""
        return {
            'id': self.id,
            'number': self.number,
            'reason': self.reason,
            'created_at': self.created_at.isoformat()
        }

class Transaction(db.Model):
    """交易记录模型"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # 金额（正为充值，负为消费）
    balance = db.Column(db.Float, nullable=False)  # 交易后余额
    type = db.Column(db.String(20), nullable=False)  # topup, consume, refund
    description = db.Column(db.Text)
    reference_id = db.Column(db.String(100))  # 订单号或其他引用ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """将交易记录对象转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'balance': self.balance,
            'type': self.type,
            'description': self.description,
            'reference_id': self.reference_id,
            'created_at': self.created_at.isoformat()
        }

class PhoneRequest(db.Model):
    """号码请求模型"""
    __tablename__ = 'phone_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, used, completed, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = db.relationship('User', backref='phone_requests')
    project = db.relationship('Project', backref='phone_requests')
    sms_messages = db.relationship('SMS', backref='phone_request', lazy=True)
    
    def to_dict(self):
        """将号码请求对象转换为字典"""
        return {
            'id': self.id,
            'request_id': self.request_id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'phone_number': self.phone_number,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class SMS(db.Model):
    """短信模型"""
    __tablename__ = 'sms_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_request_id = db.Column(db.Integer, db.ForeignKey('phone_requests.id'), nullable=False)
    sender = db.Column(db.String(50))
    content = db.Column(db.Text, nullable=False)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """将短信对象转换为字典"""
        return {
            'id': self.id,
            'phone_request_id': self.phone_request_id,
            'sender': self.sender,
            'content': self.content,
            'received_at': self.received_at.isoformat()
        } 