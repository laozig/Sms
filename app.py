#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from app import create_app
from app.services.monitoring import metrics_collector

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    # 打印启动信息
    print("SMS接码平台API系统已启动，监听端口 5000...")
    app.logger.info("SMS接码平台API系统已启动")
    
    # 导出指标的钩子
    @app.teardown_appcontext
    def export_metrics_on_shutdown(exception=None):
        if exception:
            app.logger.error(f"应用关闭时发生异常: {str(exception)}")
        
        # 导出指标
        try:
            metrics_file = metrics_collector.export_metrics()
            app.logger.info(f"指标已导出到: {metrics_file}")
        except Exception as e:
            app.logger.error(f"导出指标时发生错误: {str(e)}")
    
    # 启动应用
    # - debug=True: 启用调试模式
    # - host='0.0.0.0': 监听所有IP地址
    # - threaded=True: 使用线程处理请求
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) 