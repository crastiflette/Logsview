from flask import Flask
from flask_bcrypt import Bcrypt
from app.db import get_db

app = Flask(__name__)
bcrypt = Bcrypt(app)

def add_machine(ip, nom, passphrase):
    IP = ip
    NOM = nom
    PASWD = passphrase
    db = get_db()
    cursor = db.cursor()

    # Verifie si la machine existe déjà
    cursor.execute(
        "SELECT id FROM machines WHERE nom = %s",
        (NOM,)
    )

    if cursor.fetchone():
        raise ValueError("La machine existe déjà.")
    else:
        cursor.execute(
            "INSERT INTO machines (ip, nom, passwd) VALUES (%s, %s, %s)",
            (IP, NOM, PASWD)
        )
        db.commit()

    cursor.close()
    db.close()

    db = get_db()
    cursor = db.cursor()
