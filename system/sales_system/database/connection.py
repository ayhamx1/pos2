import psycopg2

try:
    from config.db_config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
except ImportError:
    # fallback مؤقت لو ملف الإعدادات مش موجود
    DB_HOST = "127.0.0.1"
    DB_PORT = "5432"
    DB_NAME = "pos_db"
    DB_USER = "postgres"
    DB_PASSWORD = "123456"


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )