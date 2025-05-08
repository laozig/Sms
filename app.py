import os
from app import create_app

# 创建Flask应用
app = create_app()

if __name__ == '__main__':
    # 运行应用
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    app.run(host=host, port=port, debug=debug) 