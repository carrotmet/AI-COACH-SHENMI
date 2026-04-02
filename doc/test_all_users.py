# -*- coding: utf-8 -*-
"""测试所有用户的密码"""
import bcrypt
import sqlite3

conn = sqlite3.connect('D:/github.com/carrotmet/SMAICOACH/shenmi4/data/ai_coach.db')
cursor = conn.cursor()
cursor.execute('SELECT id, username, email, password_hash FROM users ORDER BY id')
users = cursor.fetchall()
conn.close()

print(f'数据库中共有 {len(users)} 个用户:\n')

for user in users:
    user_id, username, email, password_hash = user
    print(f'ID:{user_id}, 用户名:{username}, 邮箱:{email}')
    print(f'  哈希: {password_hash[:55]}...')
    
    # 尝试一些可能的密码
    possible_passwords = ['test123456', 'test123', 'password', 'admin123', '123456', 'admin', 'test']
    matched = False
    for pwd in possible_passwords:
        try:
            result = bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8'))
            if result:
                print(f'  -> 密码是: "{pwd}"')
                matched = True
                break
        except:
            pass
    if not matched:
        print(f'  -> 未知密码')
    print()
