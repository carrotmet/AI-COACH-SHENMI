# -*- coding: utf-8 -*-
"""测试密码验证"""
import bcrypt
import sqlite3

# 获取数据库中的用户
conn = sqlite3.connect('D:/github.com/carrotmet/SMAICOACH/shenmi4/data/ai_coach.db')
cursor = conn.cursor()
cursor.execute('SELECT id, username, email, password_hash FROM users LIMIT 5')
users = cursor.fetchall()
conn.close()

print('测试密码验证:')
test_passwords = ['test123', 'admin123', 'password', '123456', 'admin', 'test', '']

for user in users:
    user_id, username, email, password_hash = user
    print(f'\n用户: {username} ({email})')
    print(f'哈希: {password_hash[:50]}...')
    
    for pwd in test_passwords:
        try:
            result = bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8'))
            if result:
                print(f'  密码 "{pwd}" -> 匹配!')
        except Exception as e:
            print(f'  密码 "{pwd}" -> 错误: {e}')
