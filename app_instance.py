#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask

# 创建Flask应用
app = Flask(__name__)

# 设置编码和CORS
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# 处理CORS和中文编码
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE')
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response 