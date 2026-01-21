import mysql.connector
import local_settings as S

def get_db():
    return mysql.connector.connect(
        host=S.DB_HOST,
        user=S.DB_USER,
        password=S.DB_PASSWORD,
        database=S.DB_NAME
    )
