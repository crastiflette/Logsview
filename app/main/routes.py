from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from functools import wraps
from config import CFG
import create_user
from app.auth.services import toutlesloubards, toutlescranks
from app.db import get_db
from get_files import get_files
from add_machine import add_machine
from traitement import process_syslog_files
from datetime import datetime

main_bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))

        if session.get('role_id') != 3:
            abort(403)  # Accès interdit

        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))

        if session.get('role_id') not in [2, 3]:
            abort(403)  # Accès interdit

        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/home')
@login_required
def home():
    
    return render_template('home.html')


@main_bp.route('/logs')
@login_required
def logs():
    required_keys = {"log_files", "local_log_dir"}
    missing = required_keys - CFG.keys()
    if missing:
        error=(f"Missing configuration keys: {missing} in config.py")
        return render_template('logs.html', error=error)

    # Récupère la liste des machines depuis la base de données
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT nom FROM machines")
    machines = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()

    return render_template('logs.html', machines=machines)

@main_bp.route('/logs/view', methods=['GET', 'POST'])
@login_required
def logs_view():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT nom FROM machines")
    machines = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()

    # Récupération des machines sélectionnées
    hosts = request.form.getlist('hosts')
    selected = [h for h in hosts if h in machines]
    if not selected:
        return redirect(url_for('main.logs'))

    # Récupération du champ 'limit' depuis le formulaire POST
    try:
        max_events = int(request.form.get('limit', 50))
    except (ValueError, TypeError):
        max_events = 50
    max_events = max(1, min(max_events, 500))

    all_events = []

    # Récupération des logs pour chaque machine et ajout d'une clé 'host'
    for host in selected:
        try:
            file_paths = get_files(host)
            events = process_syslog_files(file_paths)

            # Ajoute le nom de la machine sur chaque événement
            for e in events:
                e["host"] = host
            all_events.extend(events)
        except Exception as e:
            all_events.append({
                "timestamp": None,
                "message": f"Erreur récupération logs: {e}",
                "host": host
            })

    # Tri décroissant par timestamp
    all_events.sort(
        key=lambda e: e["timestamp"] or datetime.min,
        reverse=True
    )

    # Limite au nombre d'événements choisis
    all_events = all_events[:max_events]

    return render_template(
        'logs_view.html',
        events=all_events,  # Une seule liste
        journal_type="syslog",
        machines=machines,
        max_events=max_events
    )


@main_bp.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():

    error_message = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role_id = request.form.get('role_id')
        
        try:
            create_user.create_user(username, password, role_id)
        except ValueError as e:
            error_message = str(e)

    users = toutlesloubards()
    return render_template('admin.html', users=users, error=error_message)



@main_bp.route('/admin/delete_user/<username>', methods=['POST'])
@login_required
@admin_required
def delete_user(username):
    from delete_user import delete_user

    delete_user(username)
    return redirect(url_for('main.admin'))


@main_bp.route('/gestion', methods=['GET', 'POST'])
@login_required
@manager_required
def gestion():
    error_message = None

    if request.method == 'POST':
        ip = request.form.get('ip')
        nom = request.form.get('nom')
        password = request.form.get('password')

        try:
            add_machine(ip, nom, password)
        except ValueError as e:
            error_message = str(e)

    machines = toutlescranks()

    return render_template('gestion.html', machines=machines, error=error_message)

@main_bp.route('/gestion/delete_machine/<ip>', methods=['POST'])
@login_required
@manager_required
def delete_machine(ip):
    from remove_machine import remove_machine

    remove_machine(ip)
    return redirect(url_for('main.gestion'))