# -*- coding: utf-8 -*-
"""测试最新注册用户的密码"""
import bcrypt
import sqlite3

conn = sqlite3.connect('D:/github.com/carrotmet/SMAICOACH/shenmi4/data/ai_coach.db')
cursor = conn.cursor()
cursor.execute('SELECT id, username, email, password_hash FROM users ORDER BY id DESC LIMIT 1')
user = cursor.fetchone()
conn.close()

if user:
    user_id, username, email, password_hash = user
    print(f'最新用户 ID:{user_id}, 用户名:{username}, 邮箱:{email}')
    print(f'密码哈希: {password_hash}')
    
    # 测试常见密码
    test_passwords = ['test123456', 'password', '123456', 'test', 'admin123']
    for pwd in test_passwords:
        result = bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8'))
        print(f'  "{pwd}" -> {"匹配!" if result else "不匹配"}')
