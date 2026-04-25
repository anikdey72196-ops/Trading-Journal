import pytest
import os
import sys

# Add the app/routes directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'routes')))

from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    # We need to configure a local test db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_logout_get_method_not_allowed(client):
    response = client.get('/logout')
    assert response.status_code == 405

def test_logout_post_method_success(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.post('/logout')
    assert response.status_code == 302 # Redirect to login
    assert response.headers['Location'] == '/login'

    with client.session_transaction() as sess:
        assert 'user_id' not in sess
