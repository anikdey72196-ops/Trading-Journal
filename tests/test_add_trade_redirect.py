import pytest
from flask import Flask, session
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath('./app/routes'))

from main_routes import main_bp
from database import db, User

@pytest.fixture
def app():
    app = Flask(__name__, template_folder='../app/templates')
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    db.init_app(app)
    app.register_blueprint(main_bp, url_prefix='')

    with app.app_context():
        db.create_all()
        # Create a mock user
        user = User(Name="TestUser", Email="test@test.com", Password="hashed", Daily_max_trade=5)
        db.session.add(user)
        db.session.commit()

        yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_add_trade_redirects_when_no_daily_target(client, app):
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.get('/add_trade')

    assert response.status_code == 302
    assert '/set_daily_target' in response.location
