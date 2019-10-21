from flask import Flask, render_template
from flask_login import current_user
from flask_wtf.csrf import CSRFError

from CSDN.blueprints.admin import admin_bp
from CSDN.blueprints.auth import auth_bp
from CSDN.blueprints.main import main_bp
from CSDN.blueprints.user import user_bp
from CSDN.extensions import moment, bootstrap, login_manager, csrf, ckeditor, mail, whooshee
from CSDN.models import db, Notification


def create_app():
    app = Flask(__name__)
    app.config.from_object('CSDN.setting')
    app.config.from_object('CSDN.secret')

    register_blueprints(app)
    register_extensions(app)
    register_errorhandlers(app)
    register_template_context(app)

    return app


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')


def register_extensions(app):
    moment.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app)
    whooshee.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_to_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_sever_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 500


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
        else:
            notification_count = None
        return dict(notification_count=notification_count)