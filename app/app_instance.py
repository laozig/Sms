#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
该模块用于提供Flask应用实例。
它允许其他模块导入全局应用实例，避免循环导入问题。
"""

from flask import Flask

# 全局应用实例
app = Flask(__name__)

def set_app(flask_app):
    """设置全局应用实例"""
    global app
    app = flask_app
    return app

def get_app():
    """获取全局应用实例"""
    global app
    return app 