#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.tasks import celery
from app.database import db
from app.models.number import PhoneNumber, Message, NumberStatus
import logging
import time
import random
import re
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

@celery.task(name='tasks.fetch_sms', bind=True, max_retries=3)
def fetch_sms(self, request_id):
    """异步任务：获取短信消息"""
    logger.info(f"开始获取短信，请求ID: {request_id}")
    
    session = db.get_session()
    try:
        # 查找号码记录
        phone_number = session.query(PhoneNumber).filter_by(request_id=request_id).first()
        if not phone_number:
            logger.error(f"找不到请求ID为 {request_id} 的号码记录")
            return {'status': 'error', 'message': '找不到号码记录'}
        
        # 如果号码状态不是活跃状态，返回错误
        if phone_number.status != NumberStatus.ACTIVE:
            logger.warning(f"号码 {phone_number.number} 状态不是活跃状态，当前状态: {phone_number.status}")
            return {'status': 'error', 'message': f"号码状态不是活跃状态，当前状态: {phone_number.status}"}
        
        # 模拟从外部API获取短信的过程
        time.sleep(2)  # 模拟网络延迟
        
        # 随机生成一条短信（在实际应用中，这里应该调用外部API）
        if random.random() < 0.8:  # 80%的概率收到短信
            senders = ["10010", "10086", "10000", "95588", "106"]
            sender = random.choice(senders) + "".join([str(random.randint(0, 9)) for _ in range(5)])
            
            # 随机生成验证码
            code = "".join([str(random.randint(0, 9)) for _ in range(6)])
            templates = [
                f"您的验证码是{code}，5分钟内有效，请勿泄露给他人。",
                f"您正在登录，验证码{code}，请勿泄露给他人。",
                f"您的验证码为{code}，有效期10分钟，请勿告知他人。",
                f"验证码{code}，用于身份验证，请勿转发他人。"
            ]
            content = random.choice(templates)
            
            # 创建消息记录
            message = Message(
                phone_number_id=phone_number.id,
                sender=sender,
                content=content,
                code=code
            )
            session.add(message)
            
            # 更新号码记录的消息计数
            phone_number.message_count += 1
            
            # 提交事务
            session.commit()
            
            logger.info(f"成功获取短信，号码: {phone_number.number}，验证码: {code}")
            return {
                'status': 'success',
                'message': '成功获取短信',
                'sms': {
                    'id': message.id,
                    'sender': sender,
                    'content': content,
                    'code': code,
                    'received_at': datetime.utcnow().isoformat()
                }
            }
        else:
            logger.info(f"暂无新短信，号码: {phone_number.number}")
            return {'status': 'pending', 'message': '暂无新短信'}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"获取短信时发生数据库错误: {str(e)}")
        # 重试任务
        self.retry(exc=e, countdown=5)
    except Exception as e:
        session.rollback()
        logger.error(f"获取短信时发生未知错误: {str(e)}")
        return {'status': 'error', 'message': f'发生错误: {str(e)}'}
    finally:
        db.close_session()

@celery.task(name='tasks.release_number', bind=True)
def release_number(self, request_id):
    """异步任务：释放号码"""
    logger.info(f"开始释放号码，请求ID: {request_id}")
    
    session = db.get_session()
    try:
        # 查找号码记录
        phone_number = session.query(PhoneNumber).filter_by(request_id=request_id).first()
        if not phone_number:
            logger.error(f"找不到请求ID为 {request_id} 的号码记录")
            return {'status': 'error', 'message': '找不到号码记录'}
        
        # 更新号码状态为已释放
        phone_number.status = NumberStatus.RELEASED
        
        # 提交事务
        session.commit()
        
        logger.info(f"成功释放号码，号码: {phone_number.number}")
        return {'status': 'success', 'message': f'成功释放号码 {phone_number.number}'}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"释放号码时发生数据库错误: {str(e)}")
        return {'status': 'error', 'message': f'数据库错误: {str(e)}'}
    except Exception as e:
        session.rollback()
        logger.error(f"释放号码时发生未知错误: {str(e)}")
        return {'status': 'error', 'message': f'发生错误: {str(e)}'}
    finally:
        db.close_session()

@celery.task(name='tasks.extract_code_from_sms')
def extract_code_from_sms(message_id):
    """从短信内容中提取验证码"""
    session = db.get_session()
    try:
        # 查找消息记录
        message = session.query(Message).get(message_id)
        if not message or not message.content:
            return None
        
        # 使用正则表达式提取数字验证码
        patterns = [
            r'验证码[是为：:\s]+(\d{4,6})',
            r'码[是为：:\s]+(\d{4,6})',
            r'[code|CODE|Code][是为：:\s]+(\d{4,6})',
            r'[\[【](\d{4,6})[\]】]',
            r'(\d{4,6})'  # 最后尝试提取4-6位数字
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.content)
            if match:
                code = match.group(1)
                if code:
                    # 更新消息记录中的验证码字段
                    message.code = code
                    session.commit()
                    return code
        
        return None
    except Exception as e:
        logger.error(f"提取验证码时发生错误: {str(e)}")
        return None
    finally:
        db.close_session() 