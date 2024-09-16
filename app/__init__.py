# app/__init__.py

from flask import Flask
from flask_migrate import Migrate
from config import Config
from app.extensions import db, jwt, login_manager, api
from sqlalchemy import text
import logging

migrate = Migrate()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)
    api.init_app(app)
    migrate.init_app(app, db)

    # Configure login_manager
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'

    #with app.app_context(): # Removed, handled by migrate
        # Import models here to avoid circular imports
        #from app import models # This import is not needed because the models are imported in the routes.py file
        #print("Creating tables")
        # Create tables
        #db.create_all()
        #db.session.commit()
        #print("Tables created")

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))

    # Import and register blueprints here
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Set up API routes
    from app.routes import init_api
    init_api(api)
    
    logger.info("Application created successfully with config: %s", config_class)

    return app

# Make sure create_app is available when importing from app
__all__ = ['create_app']