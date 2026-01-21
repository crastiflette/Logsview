from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import local_settings as S

def create_app():
    app = Flask(__name__)

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp

    app.secret_key = S.SECRET_KEY
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
