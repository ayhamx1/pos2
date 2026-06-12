import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bcrypt
from database.connection import get_connection

def create_admin():
    username = "admin"
    password = "admin123"  # ممكن تغيره
    full_name = "المدير العام"
    role = "admin"
    
    # تشفير كلمة المرور
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # حذف الـ admin القديم لو موجود
        cur.execute("DELETE FROM users WHERE username = %s", (username,))
        
        # إضافة الجديد
        cur.execute("""
            INSERT INTO users (username, password, full_name, role) 
            VALUES (%s, %s, %s, %s)
        """, (username, hashed.decode('utf-8'), full_name, role))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ تم إنشاء المستخدم بنجاح!")
        print(f"   اسم المستخدم: {username}")
        print(f"   كلمة المرور: {password}")
    except Exception as e:
        print(" خطأ:", e)

if __name__ == "__main__":
    create_admin()