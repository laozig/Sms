#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.config import get_config
from celery import Celery

# 创建Celery实例
celery = Celery('sms_platform')

# 从配置中加载Celery配置
config = get_config()
celery.conf.update(
    broker_url=config.CELERY_BROKER_URL,
    result_backend=config.CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True
)

# 导入任务模块，确保Celery可以发现任务
from app.tasks import sms_tasks, notification_tasks 