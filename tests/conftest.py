# tests/conftest.py

import pytest
from app import create_app
from app.extensions import db as _db
from config import TestConfig
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope='session')
def app():
    app = create_app(config_class=TestConfig)
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def db(app):
    _db.app = app
    with app.app_context():
        _db.create_all()
    yield _db
    _db.drop_all()

@pytest.fixture(scope='function')
def client(app, db):
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='function')
def session(db):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session(bind=connection)

    yield session

    session.remove()
    transaction.rollback()
    connection.close()
