import os
from fabric import Connection
from paramiko.ssh_exception import NoValidConnectionsError, SSHException, AuthenticationException
from config import CFG
from app.db import get_db

def get_adress(server):
    """
    Récupère l'adresse IP d'un serveur depuis la base de données.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT ip FROM machines WHERE nom = %s",
        (server,)
    )
    result = cursor.fetchone()
    cursor.close()
    db.close()

    if result:
        return result[0]
    else:
        raise ValueError(f"Le serveur '{server}' n'existe pas dans la base de données.")

def get_passphrase(server):
    """
    Récupère le mot de passe SSH d'un serveur depuis la base de données.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT passwd FROM machines WHERE nom = %s",
        (server,)
    )
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result:
        return result[0]
    else:
        raise ValueError(f"Le serveur '{server}' n'existe pas dans la base de données.")

def get_files(server):
    """
    Récupère des fichiers de logs depuis un serveur distant via SSH.
    """
    retrieved_files = []
    server_ip = get_adress(server)
    log_files = CFG.get("log_files", [])
    local_dir = CFG.get("local_log_dir", ".")

    if not log_files:
        print("Warning: no log files defined in configuration.")
        return retrieved_files

    os.makedirs(local_dir, exist_ok=True)

    passphrase = get_passphrase(server)
    ssh_user = CFG.get('ssh_user', 'sae302')

    # config key -> clés présentes -> mot de passe
    key_candidates = [os.path.expanduser('~/.ssh/id_rsa'), os.path.expanduser('~/.ssh/id_ed25519')]
    existing_keys = [k for k in key_candidates if os.path.exists(k)]

    strategies = []

    # 1) clé dans config.py
    cfg_key = CFG.get('ssh_key_path')
    if cfg_key:
        cfg_key = os.path.expanduser(cfg_key)
        if os.path.exists(cfg_key) and os.access(cfg_key, os.R_OK):
            strategies.append(('config_key', {'key_filename': cfg_key, 'passphrase': passphrase, 'allow_agent': False, 'look_for_keys': False}))
        else:
            print(f"Warning: configured ssh_key_path '{cfg_key}' not found or not readable; skipping it.")

    # 3) clés détectées automatiquement
    for key in existing_keys:
        if os.path.abspath(key) == os.path.abspath(cfg_key) if cfg_key else False:
            continue
        strategies.append(('key', {'key_filename': key, 'passphrase': passphrase, 'allow_agent': False, 'look_for_keys': False}))

    auth_tried = []
    connected = False

    for name, kwargs in strategies:
        try:
            key_info = kwargs.get('key_filename') if kwargs else None
            print(f"Trying auth method '{name}' for {server} with user '{ssh_user}' (key={key_info}, agent={have_agent})")

            with Connection(server_ip, user=ssh_user, connect_kwargs=kwargs or {}) as link:
                for remote_path in log_files:
                    try:
                        local_path = os.path.join(
                            local_dir,
                            f"{server}_{os.path.basename(remote_path)}"
                        )

                        try:
                            link.get(remote_path, local=local_path)

                            # mettre le fichier readable pour l'app
                            try:
                                os.chmod(local_path, 0o644)
                            except Exception as chmod_e:
                                print(f"Warning: could not chmod {local_path}: {chmod_e}")

                            retrieved_files.append(local_path)

                        except PermissionError as e:
                            print(f"Permission denied retrieving {remote_path} from {server}: {e}")
                        except Exception as e:
                            print(f"Error retrieving {remote_path} from {server}: {e}")

                    except FileNotFoundError:
                        print(f"Warning: file not found on {server}: {remote_path}")

            connected = True
            break

        except AuthenticationException as e:
            auth_tried.append(name)
            print(f"Authentication failed ({name}) for {server}: {e}")
            continue
        except NoValidConnectionsError:
            print(f"Error: no valid connection to {server}.")
            break
        except SSHException as e:
            print(f"Error (SSH) during {name} auth for {server}: {e}")
            break

    if not connected:
        print(f"Error: Authentication failed for {server} (tried: {', '.join(auth_tried)})")

    return retrieved_files
