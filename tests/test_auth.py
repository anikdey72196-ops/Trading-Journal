import pytest
from app.routes.app import app, db
from app.routes.database import User

@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()

def test_login_required_redirect(client):
    response = client.get('/home', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_register_and_login_flow(client, test_app):
    # Register
    res = client.post('/register', data={
        'Name': 'Test Trader',
        'Email': 'trader@example.com',
        'Password': 'securepassword123',
        'Avg_Daily_max_trade': 5
    }, follow_redirects=True)
    assert res.status_code == 200

    # Verify user created in DB
    with test_app.app_context():
        user = db.session.query(User).filter_by(Email='trader@example.com').first()
        assert user is not None
        assert user.Name == 'Test Trader'

    # Login
    res = client.post('/login', data={
        'Email': 'trader@example.com',
        'Password': 'securepassword123'
    }, follow_redirects=False)
    assert res.status_code == 302
    assert '/home' in res.location

    # Logout
    res = client.get('/logout', follow_redirects=False)
    assert res.status_code == 302
    assert '/login' in res.location
