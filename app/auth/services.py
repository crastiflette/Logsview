from app.db import get_db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def quiétil(username, password):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, username, mdp_hash, role_id FROM user WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()
    cursor.close()
    db.close()

    if not user:
        return None


    
    if not bcrypt.check_password_hash(user["mdp_hash"], password):
        return None


    return user

def eskiladroit(role_id, required_role_id):

    return role_id >= required_role_id

def toutlesloubards():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT username, role_id, created_at FROM user ORDER BY username"
    )

    users = cursor.fetchall()

    cursor.close()
    db.close()

    return users

def toutlescranks():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT ip, nom FROM machines ORDER BY ip"
    )

    machines = cursor.fetchall()

    cursor.close()
    db.close()

    return machines