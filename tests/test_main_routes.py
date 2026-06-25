import pytest
from unittest.mock import patch, MagicMock
from app.routes.app import app, db
from app.routes.database import User
from app.routes.main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD
import app.routes.main_routes as main_routes

@pytest.fixture
def test_app():
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test_secret',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture(autouse=True)
def reset_cache():
    main_routes._inr_per_usd_cache = None
    main_routes._inr_per_usd_cache_time = 0



@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {'rates': {'INR': 83.5}}
    mock_get.return_value = mock_response

    result = get_inr_per_usd()

    assert result == 83.5
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_exception(mock_get):
    mock_get.side_effect = Exception("API Error")

    result = get_inr_per_usd()

    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_invalid_json(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {'unexpected_key': 'value'}
    mock_get.return_value = mock_response

    result = get_inr_per_usd()

    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

def test_set_daily_target_db_error(test_app, client):
    # Do setup first, before mocking commit
    with test_app.app_context():
        user = User(Name='testuser', Email='test@example.com', Password='password', Daily_max_trade=5)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['user_id'] = user_id

    # Now mock commit and rollback
    with patch('app.routes.main_routes.db.session.commit') as mock_commit, \
         patch('app.routes.main_routes.db.session.rollback') as mock_rollback:

        mock_commit.side_effect = Exception("DB Error")

        response = client.post('/set_daily_target', data={'max_trades': 5}, follow_redirects=True)

        assert b'Failed to set daily target. Try again.' in response.data

        assert response.status_code == 200
        mock_rollback.assert_called_once()
