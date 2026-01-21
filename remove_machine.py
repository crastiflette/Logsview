from flask import Flask
from app.db import get_db

def remove_machine(nom):
    NOM = nom

    db = get_db()
    cursor = db.cursor()

    # On verifie que la machine existe
    cursor.execute(
        "SELECT id FROM machines WHERE nom = %s",
        (NOM,)
    )

    if cursor.fetchone():
        cursor.execute(
            "DELETE FROM machines WHERE nom=%s",
            (NOM,)
        )
        db.commit()
    else:
        raise ValueError("La machine n'existe pas.")
        

    cursor.close()
    db.close()