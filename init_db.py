#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import random
from datetime import datetime

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入应用和模型
from app import create_app
from app.database import db
from app.models.user import User
from app.models.project import Project
from app.models.number import PhoneNumber, Message, NumberStatus

def init_db():
    """初始化数据库"""
    # 创建应用实例
    app = create_app()
    
    with app.app_context():
        logger.info("开始初始化数据库...")
        
        # 删除并重新创建所有表
        db.drop_all()
        db.create_all()
        
        logger.info("数据库表已重新创建")
        
        # 创建管理员用户
        admin = User(
            username="admin",
            email="admin@example.com",
            is_admin=True,
            is_active=True,
            balance=1000.0,
        )
        admin.password = "admin123"
        
        # 创建测试用户
        test_user = User(
            username="test",
            email="test@example.com",
            is_admin=False,
            is_active=True,
            balance=100.0,
        )
        test_user.password = "test123"
        
        # 添加用户到数据库
        session = db.get_session()
        try:
            session.add_all([admin, test_user])
            session.commit()
            logger.info("初始用户已创建")
            
            # 创建测试项目
            projects = []
            for i in range(1, 6):
                is_exclusive = (i % 3 == 0)  # 每3个项目中的1个是专属项目
                exclusive_id = f"excl_{i}" if is_exclusive else None
                
                project = Project(
                    name=f"测试项目 {i}",
                    code=f"test_project_{i}",
                    price=round(random.uniform(0.5, 5.0), 2),
                    description=f"这是测试项目 {i} 的描述",
                    success_rate=round(random.uniform(0.7, 0.99), 2),
                    available=True,
                    is_exclusive=is_exclusive,
                    exclusive_id=exclusive_id
                )
                projects.append(project)
            
            # 添加项目到数据库
            session.add_all(projects)
            session.commit()
            logger.info(f"已创建 {len(projects)} 个测试项目")
            
            # 创建测试号码和短信
            phone_numbers = []
            messages = []
            
            # 为测试用户创建一些号码记录
            for i in range(3):
                phone_number = PhoneNumber(
                    request_id=f"req_{test_user.id}_{i}_{int(datetime.now().timestamp())}",
                    number=f"1{random.randint(3, 9)}{random.randint(100000000, 999999999)}",
                    project_id=projects[i].id,
                    user_id=test_user.id,
                    price=projects[i].price,
                    status=NumberStatus.ACTIVE if i < 2 else NumberStatus.COMPLETED,
                    message_count=random.randint(0, 3)
                )
                phone_numbers.append(phone_number)
            
            # 添加号码到数据库
            session.add_all(phone_numbers)
            session.commit()
            
            # 为号码创建短信
            for phone in phone_numbers:
                for j in range(phone.message_count):
                    # 随机生成验证码
                    code = "".join([str(random.randint(0, 9)) for _ in range(6)])
                    
                    # 随机生成发送者
                    senders = ["10010", "10086", "10000", "95588", "106"]
                    sender = random.choice(senders) + "".join([str(random.randint(0, 9)) for _ in range(5)])
                    
                    # 随机生成内容
                    templates = [
                        f"您的验证码是{code}，5分钟内有效，请勿泄露给他人。",
                        f"您正在登录，验证码{code}，请勿泄露给他人。",
                        f"您的验证码为{code}，有效期10分钟，请勿告知他人。",
                        f"验证码{code}，用于身份验证，请勿转发他人。"
                    ]
                    content = random.choice(templates)
                    
                    message = Message(
                        phone_number_id=phone.id,
                        sender=sender,
                        content=content,
                        code=code
                    )
                    messages.append(message)
            
            # 添加短信到数据库
            if messages:
                session.add_all(messages)
                session.commit()
                logger.info(f"已创建 {len(messages)} 条测试短信")
            
            logger.info("数据库初始化完成")
        
        except Exception as e:
            session.rollback()
            logger.error(f"初始化数据库时发生错误: {str(e)}")
            raise
        finally:
            db.close_session()

if __name__ == "__main__":
    init_db() 