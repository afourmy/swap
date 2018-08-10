from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from swap.routes import swap


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.register_blueprint(swap)
    db.init_app(app)
    configure_database(app)
    return app
