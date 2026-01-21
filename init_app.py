import os
import getpass
import mysql.connector
import sys

import local_settings as S

DUMP_PATH = os.path.join(os.path.dirname(__file__), "sauvegarde.sql")


def connect_as_root():
    root_user = S.DB_ROOT_USER
    root_password = S.DB_ROOT_PASSWORD

    if root_password == "":
        root_password = getpass.getpass(f"MariaDB password for '{root_user}': ")

    return mysql.connector.connect(
        host=S.DB_HOST,
        user=root_user,
        password=root_password,
        autocommit=True,
    )


def ensure_db_and_user(root_db):
    db_name = S.DB_NAME
    app_user = S.DB_USER
    app_password = S.DB_PASSWORD

    cursor = root_db.cursor()

    # 1) Créer la base de données
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")

    # 2) Créer l'utilisateur (MariaDB/MySQL : IF NOT EXISTS est pris en charge sur les versions récentes ; en cas d'échec, on applique une solution de secours)
    try:
        cursor.execute(f"CREATE USER IF NOT EXISTS '{app_user}'@'%' IDENTIFIED BY %s;", (app_password,))
    except mysql.connector.Error:
        # Solution de secours : vérifier si l'utilisateur existe, puis le créer s'il manque
        cursor.execute("SELECT 1 FROM mysql.user WHERE user = %s;", (app_user,))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE USER '{app_user}'@'%' IDENTIFIED BY %s;", (app_password,))

    # 3) Accorder les privilèges
    cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{app_user}'@'%';")
    cursor.execute("FLUSH PRIVILEGES;")

    cursor.close()


def run_sql_file(app_db, path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"SQL dump not found: {path}")

    cursor = app_db.cursor()

    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    statements = []
    buff = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("--") or stripped.startswith("/*") or stripped.startswith("*/"):
            continue
        buff.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buff))
            buff = []

    # Exécuter les requêtes
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error as e:
            # Si le dump contient des CREATE TABLE IF NOT EXISTS, etc., c'est acceptable ; sinon, on remonte l'erreur
            raise RuntimeError(f"SQL error: {e}\nStatement:\n{stmt[:500]}...") from e

    app_db.commit()
    cursor.close()


def ensure_admin_user():
    # Utilise votre utilitaire existant qui vérifie déjà l'existence
    import create_user

    admin_username = "admin"
    admin_password = "admin"
    admin_role_id = 3

    try:
        create_user.create_user(admin_username, admin_password, admin_role_id)
        print("Admin user created: admin/admin")
    except ValueError as e:
        # "L'utilisateur existe déjà."
        print(f"Admin user already exists: {e}")

def database_has_tables(conn, db_name):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s;",
        (db_name,)
    )
    count = cursor.fetchone()[0]
    cursor.close()
    return count > 0


def reset_database(root_db, db_name):
    cursor = root_db.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`;")
    cursor.execute(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
    cursor.close()

def main():
    print("=== LogsView init ===")
    print(f"DB host: {S.DB_HOST}:{getattr(S, 'DB_PORT', 3306)}")
    print(f"DB name: {S.DB_NAME}")
    print(f"DB user: {S.DB_USER}")

    reset_mode = "--annihilate" in sys.argv

    # 1) Root connect: ensure DB/user, and optionally reset DB
    root_db = connect_as_root()
    try:
        ensure_db_and_user(root_db)

        if reset_mode:
            print("Reset mode enabled: dropping and recreating the database.")
            reset_database(root_db, S.DB_NAME)

    finally:
        root_db.close()

    # 2) Connect as app user
    app_db = mysql.connector.connect(
        host=S.DB_HOST,
        user=S.DB_USER,
        password=S.DB_PASSWORD,
        database=S.DB_NAME,
    )

    try:
        # Safety: refuse to import destructive dump into non-empty DB unless --reset
        if database_has_tables(app_db, S.DB_NAME) and not reset_mode:
            raise RuntimeError(
                "Refusing to import sauvegarde.sql because the database already contains tables, and the dump contains DROP TABLE.\n"
                "To reinitialize everything (DESTRUCTIVE), run:\n"
                "  python init_app.py --annihilate"
            )

        print(f"Importing SQL dump: {DUMP_PATH}")
        run_sql_file(app_db, DUMP_PATH)
        print("SQL import OK")
    finally:
        app_db.close()

    ensure_admin_user()
    print("=== Init finished ===")

if __name__ == "__main__":
    main()