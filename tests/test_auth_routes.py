import pytest
from unittest.mock import patch
from flask import session
from werkzeug.datastructures import MultiDict
from app.routes.app import app, db
from app.routes.database import User

@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    # Needs to be called in order to initialize the db with the app, which might not be done in test contexts properly
    # db.init_app(app) # It is actually initialized in app.py

    with app.app_context():
        # Using db.create_all() inside app context creates the tables
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_register_get(test_client):
    response = test_client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

def test_register_post_success(test_client):
    response = test_client.post('/register', data=dict(
        Name='Test User',
        Email='test@example.com',
        Password='password123',
        Confirm_password='password123',
        Avg_Daily_max_trade=5
    ), follow_redirects=True)

    assert response.status_code == 200
    assert b'Registration successful!' in response.data

    with app.app_context():
        user = db.session.query(User).filter_by(Email='test@example.com').first()
        assert user is not None
        assert user.Name == 'Test User'

def test_register_post_existing_user(test_client):
    with app.app_context():
        # Create a user first
        user = User(Name='Existing User', Email='existing@example.com', Password='hashed', Daily_max_trade=5)
        db.session.add(user)
        db.session.commit()

    response = test_client.post('/register', data=dict(
        Name='New User',
        Email='existing@example.com',
        Password='password123',
        Confirm_password='password123',
        Avg_Daily_max_trade=5
    ), follow_redirects=True)

    assert response.status_code == 200
    assert b'Registration failed. Email or Username might already exist.' in response.data

def test_register_redirect_if_logged_in(test_client):
    with test_client.session_transaction() as sess:
        sess['user_id'] = 1

    response = test_client.get('/register')
    assert response.status_code == 302
    assert response.location.endswith('/home')
