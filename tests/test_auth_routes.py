import pytest
from unittest.mock import patch
from flask import Flask
from app.routes.database import db
from app.routes.auth_routes import auth_bp

@pytest.fixture
def test_app():
    # Create a fresh app for testing
    app = Flask(__name__, template_folder='../app/templates')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    db.init_app(app)
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@patch('app.routes.auth_routes.db.session.commit')
@patch('app.routes.auth_routes.db.session.rollback')
def test_register_db_error(mock_rollback, mock_commit, client, test_app):
    mock_commit.side_effect = Exception("Simulated DB error")

    response = client.post('/register', data={
        'Name': 'Test User',
        'Email': 'test@example.com',
        'Password': 'testpassword',
        'Avg_Daily_max_trade': 5
    }, follow_redirects=True)

    assert mock_commit.called
    assert mock_rollback.called
    assert b'Registration failed. Email or Username might already exist.' in response.data
