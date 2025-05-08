import sqlite3
import time
from datetime import datetime

def check_users():
    """检查并显示数据库中的用户记录"""
    # 连接到数据库
    conn = sqlite3.connect('instance/dev_sms_platform.db')
    cursor = conn.cursor()
    
    try:
        # 查询用户表
        cursor.execute("SELECT id, username, email, password, balance, created_at FROM users")
        rows = cursor.fetchall()
        
        print(f"\n==== 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")
        print(f"数据库中共有 {len(rows)} 个用户:")
        
        for row in rows:
            print(f"ID: {row[0]}, 用户名: {row[1]}, 邮箱: {row[2]}, 密码: {row[3]}, 余额: {row[4]}, 创建时间: {row[5]}")
    except Exception as e:
        print(f"查询出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("开始监控数据库中的用户表...")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            check_users()
            # 每5秒检查一次
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n监控已停止") 