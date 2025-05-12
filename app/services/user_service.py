#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.database import db
from app.models.user import User
from app.services.cache_service import cached
from app.middlewares.auth_middleware import generate_jwt_token
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class UserService:
    """用户服务，提供用户相关的业务逻辑"""
    
    @staticmethod
    def register(username, email, password):
        """注册新用户"""
        session = db.get_session()
        try:
            # 检查用户名是否已存在
            existing_user = session.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "用户名已存在"
            
            # 检查邮箱是否已存在
            existing_email = session.query(User).filter(User.email == email).first()
            if existing_email:
                return False, "邮箱已被使用"
            
            # 创建新用户
            new_user = User(
                username=username,
                email=email,
                is_admin=False,
                is_active=True,
                balance=0.0
            )
            new_user.password = password  # 使用setter方法进行哈希处理
            
            # 添加到数据库
            session.add(new_user)
            session.commit()
            
            # 生成令牌
            token = generate_jwt_token(new_user.id, new_user.username, new_user.is_admin)
            
            return True, {
                "token": token,
                "user": {
                    "id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "is_admin": new_user.is_admin,
                    "balance": new_user.balance
                }
            }
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"注册用户时发生数据库错误: {str(e)}")
            return False, f"数据库错误: {str(e)}"
        except Exception as e:
            session.rollback()
            logger.error(f"注册用户时发生未知错误: {str(e)}")
            return False, f"发生错误: {str(e)}"
        finally:
            db.close_session()
    
    @staticmethod
    def login(username, password):
        """用户登录"""
        session = db.get_session()
        try:
            # 查找用户
            user = session.query(User).filter(User.username == username).first()
            
            # 如果用户不存在或密码不正确
            if not user or not user.verify_password(password):
                return False, "用户名或密码错误"
            
            # 如果用户被禁用
            if not user.is_active:
                return False, "用户已被禁用"
            
            # 生成令牌
            token = generate_jwt_token(user.id, user.username, user.is_admin)
            
            return True, {
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin,
                    "balance": user.balance
                }
            }
        
        except Exception as e:
            logger.error(f"用户登录时发生错误: {str(e)}")
            return False, f"发生错误: {str(e)}"
        finally:
            db.close_session()
    
    @staticmethod
    @cached(ttl=60)  # 缓存1分钟
    def get_user(user_id):
        """获取用户信息"""
        session = db.get_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return None
            
            # 转换为字典并返回
            return user.to_dict()
        
        except Exception as e:
            logger.error(f"获取用户信息时发生错误: {str(e)}")
            return None
        finally:
            db.close_session()
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """更新用户资料"""
        session = db.get_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return False, "用户不存在"
            
            # 更新可编辑字段
            if "email" in profile_data:
                # 检查邮箱是否已被其他用户使用
                existing_email = session.query(User).filter(
                    User.email == profile_data["email"],
                    User.id != user_id
                ).first()
                
                if existing_email:
                    return False, "邮箱已被其他用户使用"
                
                user.email = profile_data["email"]
            
            # 提交更改
            session.commit()
            
            return True, {
                "message": "个人资料已更新",
                "user": user.to_dict()
            }
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"更新用户资料时发生数据库错误: {str(e)}")
            return False, f"数据库错误: {str(e)}"
        except Exception as e:
            session.rollback()
            logger.error(f"更新用户资料时发生未知错误: {str(e)}")
            return False, f"发生错误: {str(e)}"
        finally:
            db.close_session()
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """修改密码"""
        session = db.get_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return False, "用户不存在"
            
            # 验证旧密码
            if not user.verify_password(old_password):
                return False, "旧密码不正确"
            
            # 设置新密码
            user.password = new_password
            
            # 提交更改
            session.commit()
            
            return True, {"message": "密码已更新"}
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"修改密码时发生数据库错误: {str(e)}")
            return False, f"数据库错误: {str(e)}"
        except Exception as e:
            session.rollback()
            logger.error(f"修改密码时发生未知错误: {str(e)}")
            return False, f"发生错误: {str(e)}"
        finally:
            db.close_session()
    
    @staticmethod
    def update_balance(user_id, amount, description=""):
        """更新用户余额"""
        session = db.get_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return False, "用户不存在"
            
            # 计算新余额
            new_balance = user.balance + amount
            
            # 如果余额变为负数，则拒绝操作
            if new_balance < 0:
                return False, "余额不足"
            
            # 更新余额
            user.balance = new_balance
            
            # 提交更改
            session.commit()
            
            # 记录交易（可以在这里添加交易记录）
            
            return True, {
                "message": "余额已更新",
                "new_balance": new_balance,
                "amount": amount,
                "description": description
            }
        
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"更新余额时发生数据库错误: {str(e)}")
            return False, f"数据库错误: {str(e)}"
        except Exception as e:
            session.rollback()
            logger.error(f"更新余额时发生未知错误: {str(e)}")
            return False, f"发生错误: {str(e)}"
        finally:
            db.close_session()
    
    @staticmethod
    def get_all_users(page=1, per_page=10, filter_str=None):
        """获取所有用户（管理员功能）"""
        session = db.get_session()
        try:
            # 创建查询
            query = session.query(User)
            
            # 应用过滤
            if filter_str:
                query = query.filter(
                    (User.username.ilike(f'%{filter_str}%')) |
                    (User.email.ilike(f'%{filter_str}%'))
                )
            
            # 计算总数
            total = query.count()
            
            # 分页
            users = query.order_by(User.id).offset((page - 1) * per_page).limit(per_page).all()
            
            # 转换为字典列表
            user_list = [user.to_dict() for user in users]
            
            return {
                "items": user_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        
        except Exception as e:
            logger.error(f"获取所有用户时发生错误: {str(e)}")
            return None
        finally:
            db.close_session()

# 创建用户服务实例
user_service = UserService() 