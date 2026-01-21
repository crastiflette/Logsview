from flask import Flask
from flask_bcrypt import Bcrypt
from app.db import get_db

# Flask minimal pour initialiser bcrypt
app = Flask(__name__)
bcrypt = Bcrypt(app)

def create_user(username, password, role_id):
    USERNAME = username
    PASSWORD = password
    ROLE_ID = role_id

    password_hash = bcrypt.generate_password_hash(PASSWORD).decode("utf-8")

    db = get_db()
    cursor = db.cursor()

    # Verifie si l'utilisateur existe déjà
    cursor.execute(
        "SELECT id FROM user WHERE username = %s",
        (USERNAME,)
    )

    if cursor.fetchone():
        raise ValueError("L'utilisateur existe déjà.")
    else:
        cursor.execute(
            "INSERT INTO user (username, mdp_hash, role_id) VALUES (%s, %s, %s)",
            (USERNAME, password_hash, ROLE_ID)
        )
        db.commit()

    cursor.close()
    db.close()
