from flask import Blueprint, request, render_template, redirect, url_for, session
from app.auth.services import quiétil

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = quiétil(username, password)

        if user:
            session['user'] = user['username']
            session['role_id'] = user['role_id']
            session.permanent = True
            return redirect(url_for('main.home'))

        return render_template('form.html', error="Identifiants invalides")

    return render_template('form.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
