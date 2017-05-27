from flask import Flask

from app.model import db, login_manager
from config import SECRET_KEY, DB_URI


def create_app():
    app = Flask(__name__)
    app.register_blueprint(route)
    app.register_blueprint(api)
    app.config['SECRET_KEY'] = SECRET_KEY

    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    login_manager.init_app(app)

    return app


def init_db():
    db.create_all()

from .route import route
from .api import api
