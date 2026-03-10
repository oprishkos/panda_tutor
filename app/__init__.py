import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO()
mail = Mail()
csrf = CSRFProtect()


def create_app(config_class=None):
    app = Flask(__name__)
    if config_class is None:
        import config
        config_class = config.Config
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Войдите, чтобы получить доступ.'
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins='*')
    mail.init_app(app)

    from app.auth import auth_bp
    from app.main import main_bp
    from app.student import student_bp
    from app.tutor import tutor_bp
    from app.admin import admin_bp
    from app.chat import chat_bp
    from app.payments import payments_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(tutor_bp, url_prefix='/tutor')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(payments_bp, url_prefix='/payments')

    @app.context_processor
    def inject_stripe_key():
        return {'stripe_publishable_key': app.config.get('STRIPE_PUBLISHABLE_KEY', '')}

    return app
