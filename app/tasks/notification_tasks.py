#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.tasks import celery
from app.database import db
from app.models.user import User
import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from app.config import get_config

logger = logging.getLogger(__name__)

@celery.task(name='tasks.send_email_notification', bind=True, max_retries=3)
def send_email_notification(self, user_id, subject, content):
    """发送电子邮件通知"""
    logger.info(f"开始发送电子邮件通知，用户ID: {user_id}")
    
    session = db.get_session()
    try:
        # 查找用户
        user = session.query(User).get(user_id)
        if not user or not user.email:
            logger.error(f"找不到用户或用户没有电子邮件地址，用户ID: {user_id}")
            return {'status': 'error', 'message': '找不到用户或用户没有电子邮件地址'}
        
        # 获取SMTP配置
        config = get_config()
        smtp_server = getattr(config, 'SMTP_SERVER', 'localhost')
        smtp_port = getattr(config, 'SMTP_PORT', 25)
        smtp_username = getattr(config, 'SMTP_USERNAME', '')
        smtp_password = getattr(config, 'SMTP_PASSWORD', '')
        smtp_from = getattr(config, 'SMTP_FROM', 'noreply@example.com')
        
        # 创建消息
        msg = MIMEText(content, 'html', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = smtp_from
        msg['To'] = user.email
        
        # 发送邮件
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                
                server.sendmail(smtp_from, [user.email], msg.as_string())
                logger.info(f"已成功发送电子邮件通知，用户ID: {user_id}")
                return {'status': 'success', 'message': '已成功发送电子邮件通知'}
        
        except smtplib.SMTPException as e:
            logger.error(f"发送电子邮件时发生SMTP错误: {str(e)}")
            # 重试任务
            self.retry(exc=e, countdown=5)
    except Exception as e:
        logger.error(f"发送电子邮件通知时发生未知错误: {str(e)}")
        return {'status': 'error', 'message': f'发生错误: {str(e)}'}
    finally:
        db.close_session()

@celery.task(name='tasks.send_batch_notification', bind=True)
def send_batch_notification(self, user_ids, subject, content):
    """批量发送通知"""
    logger.info(f"开始批量发送通知，用户数量: {len(user_ids)}")
    
    # 创建子任务发送单个通知
    for user_id in user_ids:
        send_email_notification.delay(user_id, subject, content)
    
    return {'status': 'success', 'message': f'已开始发送 {len(user_ids)} 个通知'}

@celery.task(name='tasks.send_notification_to_all', bind=True)
def send_notification_to_all(self, subject, content, exclude_user_ids=None):
    """向所有用户发送通知"""
    logger.info("开始向所有用户发送通知")
    
    session = db.get_session()
    try:
        # 查询活跃用户
        query = session.query(User.id).filter(User.is_active == True)
        
        # 排除特定用户
        if exclude_user_ids:
            query = query.filter(User.id.notin_(exclude_user_ids))
        
        # 获取所有用户ID
        user_ids = [user_id for user_id, in query.all()]
        logger.info(f"找到 {len(user_ids)} 个活跃用户")
        
        # 批量发送通知
        send_batch_notification.delay(user_ids, subject, content)
        
        return {'status': 'success', 'message': f'已开始向 {len(user_ids)} 个用户发送通知'}
    except Exception as e:
        logger.error(f"向所有用户发送通知时发生错误: {str(e)}")
        return {'status': 'error', 'message': f'发生错误: {str(e)}'}
    finally:
        db.close_session() 