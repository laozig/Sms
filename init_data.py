from app import create_app
from app.models import db, User, Project, UserFavorite, UserExclusiveProject, Transaction
import random

def init_database():
    """初始化数据库"""
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        # 重建数据库
        db.drop_all()
        db.create_all()
        
        print("数据库表创建完成")
        
        # 创建管理员用户
        admin = User(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True
        )
        
        # 创建测试用户
        test_user = User(
            username="test_user",
            email="test_user@example.com",
            password="password123"
        )
        
        db.session.add(admin)
        db.session.add(test_user)
        db.session.commit()
        
        print("用户创建完成")
        
        # 创建示例项目
        projects = []
        project1 = Project(
            name="微信登录",
            code="wechat_login",
            description="微信验证码登录",
            price=1.0,
            is_exclusive=False
        )
        project1.success_rate = 0.98
        project1.available = True
        projects.append(project1)

        project2 = Project(
            name="支付宝登录",
            code="alipay_login",
            description="支付宝验证码登录",
            price=1.2,
            is_exclusive=False
        )
        project2.success_rate = 0.97
        project2.available = True
        projects.append(project2)

        project3 = Project(
            name="抖音登录",
            code="douyin_login",
            description="抖音验证码登录",
            price=1.5,
            is_exclusive=False
        )
        project3.success_rate = 0.96
        project3.available = True
        projects.append(project3)

        project4 = Project(
            name="京东登录",
            code="jd_login",
            description="京东验证码登录",
            price=1.3,
            is_exclusive=False
        )
        project4.success_rate = 0.95
        project4.available = True
        projects.append(project4)

        project5 = Project(
            name="淘宝登录",
            code="taobao_login",
            description="淘宝验证码登录",
            price=1.3,
            is_exclusive=False
        )
        project5.success_rate = 0.94
        project5.available = True
        projects.append(project5)

        project6 = Project(
            name="银行VIP",
            code="bank_vip",
            description="银行VIP专属验证码服务",
            price=5.0,
            is_exclusive=True
        )
        project6.success_rate = 0.99
        project6.available = True
        projects.append(project6)

        project7 = Project(
            name="电商VIP",
            code="ecommerce_vip",
            description="电商VIP专属验证码服务",
            price=3.0,
            is_exclusive=True
        )
        project7.success_rate = 0.98
        project7.available = True
        projects.append(project7)

        db.session.add_all(projects)
        db.session.commit()
        
        print("项目创建完成")
        
        # 让测试用户收藏几个项目
        favorites = [
            UserFavorite(user_id=test_user.id, project_id=1),
            UserFavorite(user_id=test_user.id, project_id=3),
            UserFavorite(user_id=test_user.id, project_id=5)
        ]
        
        # 让测试用户加入一个专属项目
        exclusives = [
            UserExclusiveProject(user_id=test_user.id, project_id=6)
        ]
        
        db.session.add_all(favorites)
        db.session.add_all(exclusives)
        db.session.commit()
        
        print("用户收藏和专属项目创建完成")
        
        # 为测试用户添加余额
        transaction = Transaction(
            user_id=test_user.id,
            amount=100.0,
            balance=100.0,
            type='topup',
            description='初始充值',
            reference_id=f'init_{random.randint(10000, 99999)}'
        )
        
        # 更新用户余额
        test_user.balance = 100.0
        
        db.session.add(transaction)
        db.session.commit()
        
        print("交易记录和余额更新完成")
        
        print("数据初始化完成!")

if __name__ == "__main__":
    init_database() 