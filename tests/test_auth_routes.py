import pytest
from flask import Flask
from werkzeug.security import generate_password_hash
import sys
import os

# Add app/routes to sys.path so we can import app modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/routes')))

from database import db, User
from auth_routes import auth_bp
from main_routes import main_bp
from form import Register, Login

@pytest.fixture
def app():
    app = Flask(__name__, template_folder='../app/templates')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret'

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def test_register_get(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

def test_register_post_success(client, app):
    response = client.post('/register', data={
        'Name': 'Test User',
        'Email': 'test@example.com',
        'Password': 'password123',
        'ConfirmPassword': 'password123',
        'Avg_Daily_max_trade': 5
    })

    assert response.status_code == 302
    assert response.location == '/login'

    with app.app_context():
        user = User.query.filter_by(Email='test@example.com').first()
        assert user is not None
        assert user.Name == 'Test User'

def test_register_post_failure_duplicate(client, app):
    with app.app_context():
        hashed_password = generate_password_hash('password123', method='pbkdf2:sha256')
        user = User(Name='Existing User', Email='existing@example.com', Password=hashed_password, Daily_max_trade=3)
        db.session.add(user)
        db.session.commit()

    response = client.post('/register', data={
        'Name': 'Another User',
        'Email': 'existing@example.com',
        'Password': 'password123',
        'ConfirmPassword': 'password123',
        'Avg_Daily_max_trade': 5
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Registration failed. Email or Username might already exist.' in response.data

def test_register_already_logged_in(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.get('/register')
    assert response.status_code == 302
    assert response.location == '/home'

def test_login_get(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login_post_success(client, app):
    with app.app_context():
        hashed_password = generate_password_hash('password123', method='pbkdf2:sha256')
        user = User(Name='Login User', Email='login@example.com', Password=hashed_password, Daily_max_trade=3)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    response = client.post('/login', data={
        'Email': 'login@example.com',
        'Password': 'password123'
    })

    assert response.status_code == 302
    assert response.location == '/home'

    with client.session_transaction() as sess:
        assert sess.get('user_id') == user_id

def test_login_post_failure_wrong_password(client, app):
    with app.app_context():
        hashed_password = generate_password_hash('password123', method='pbkdf2:sha256')
        user = User(Name='Login User', Email='login@example.com', Password=hashed_password, Daily_max_trade=3)
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', data={
        'Email': 'login@example.com',
        'Password': 'wrongpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data

    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_login_post_failure_non_existent_user(client):
    response = client.post('/login', data={
        'Email': 'nonexistent@example.com',
        'Password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data

    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_login_already_logged_in(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.get('/login')
    assert response.status_code == 302
    assert response.location == '/home'

def test_logout(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.get('/logout')
    assert response.status_code == 302
    assert response.location == '/login'

    with client.session_transaction() as sess:
        assert 'user_id' not in sess
