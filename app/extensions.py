# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_restful import Api

db = SQLAlchemy()
jwt = JWTManager()
login_manager = LoginManager()
api = Api()