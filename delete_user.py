from flask import Flask
from app.db import get_db

def delete_user(username):
    USERNAME = username

    db = get_db()
    cursor = db.cursor()

    # On verifie que l'utilisateur existe
    cursor.execute(
        "SELECT id FROM user WHERE username = %s",
        (USERNAME,)
    )

    if cursor.fetchone():
        cursor.execute(
            "DELETE FROM user WHERE username=%s",
            (USERNAME,)
        )
        db.commit()
    else:
        raise ValueError("L'utilisateur n'existe pas.")
        

    cursor.close()
    db.close()