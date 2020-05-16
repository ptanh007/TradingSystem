# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.

# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.

from datetime import datetime
import os

from flask import Flask, session
from flask_mail import Mail
from flask_migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager, UserMixin
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_login import login_required

import dash
import dash_core_components as dcc
import dash_html_components as html

from flask.helpers import get_root_path

# Instantiate Flask extensions
db = SQLAlchemy()
csrf_protect = CSRFProtect()
mail = Mail()
migrate = Migrate()


def create_app(extra_config_settings={}):
    """Create a Flask applicaction.
    """
    # Instantiate Flask
    app = Flask(__name__)

    # Load App Config settings
    # Load common settings from 'app/settings.py' file
    app.config.from_object('app.settings')
    # Load local settings from 'app/local_settings.py'
    app.config.from_object('app.local_settings')
    # Load extra config settings from 'extra_config_settings' param
    app.config.update(extra_config_settings)

    # Setup Flask-Extensions -- do this _after_ app config has been loaded

    # Setup Flask-SQLAlchemy
    db.init_app(app)

    # Setup Flask-Migrate
    migrate.init_app(app, db)

    # Setup Flask-Mail
    mail.init_app(app)

    # Setup session
    Session(app)

    # Setup WTForms CSRFProtect
    csrf_protect.init_app(app)

    # dash
    register_dashapps(app)
    register_stickerapp(app)
    csrf_protect._exempt_views.add('dash.dash.dispatch')

    # Register blueprints
    from app.controllers.controller1 import main_blueprint
    from app.controllers.apis import api_blueprint
    from app.controllers.controller2 import controller2_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint)
    app.register_blueprint(controller2_blueprint)
    csrf_protect.exempt(api_blueprint)
    
    # Define bootstrap_is_hidden_field for flask-bootstrap's bootstrap_wtf.html
    from wtforms.fields import HiddenField

    def is_hidden_field_filter(field):
        return isinstance(field, HiddenField)

    app.jinja_env.globals['bootstrap_is_hidden_field'] = is_hidden_field_filter

    # Setup an error-logger to send emails to app.config.ADMINS
    init_email_error_handler(app)

    # Setup Flask-User to handle user account related forms
    from .models.user_models import User, MyRegisterForm
    from .controllers.controller1 import user_profile_page

    user_manager = UserManager(app, db, User)

    return app


def init_email_error_handler(app):
    """
    Initialize a logger to send emails on error-level messages.
    Unhandled exceptions will now send an email message to app.config.ADMINS.
    """
    if app.debug: return  # Do not send error emails while developing

    # Retrieve email settings from app.config
    host = app.config['MAIL_SERVER']
    port = app.config['MAIL_PORT']
    from_addr = app.config['MAIL_DEFAULT_SENDER']
    username = app.config['MAIL_USERNAME']
    password = app.config['MAIL_PASSWORD']
    secure = () if app.config.get('MAIL_USE_TLS') else None

    # Retrieve app settings from app.config
    to_addr_list = app.config['ADMINS']
    subject = app.config.get('APP_SYSTEM_ERROR_SUBJECT_LINE', 'System Error')

    # Setup an SMTP mail handler for error-level messages
    import logging
    from logging.handlers import SMTPHandler

    mail_handler = SMTPHandler(
        mailhost=(host, port),  # Mail host and port
        fromaddr=from_addr,  # From address
        toaddrs=to_addr_list,  # To address
        subject=subject,  # Subject line
        credentials=(username, password),  # Credentials
        secure=secure,
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    # Log errors using: app.logger.error('Some error message')

def register_dashapps(app):
    from app.tradingapp.layout import layout
    from app.tradingapp.callbacks import register_callbacks

    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}

    dashapp1 = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/trading/',
                         assets_folder=get_root_path(__name__) + '/dashboard/assets/',
                         meta_tags=[meta_viewport])

    with app.app_context():
        dashapp1.title = 'QT-Trading'
        dashapp1.layout = layout
        register_callbacks(dashapp1)

    _protect_dashviews(dashapp1)

def register_stickerapp(app):
    from app.stickerapp.layout import layout
    from app.stickerapp.callbacks import register_callbacks

    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}

    dashapp2 = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/sticker/',
                         assets_folder=get_root_path(__name__) + '/dashboard/assets/',
                         meta_tags=[meta_viewport])

    with app.app_context():
        dashapp2.title = 'QT-Trading'
        dashapp2.layout = layout
        register_callbacks(dashapp2)

    _protect_dashviews(dashapp2)

def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])



