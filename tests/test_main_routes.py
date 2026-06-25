import pytest
from unittest.mock import patch, MagicMock
from app.routes import main_routes
from app.routes.main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD
from app.routes.app import app

@pytest.fixture(autouse=True)
def clear_cache():
    main_routes._inr_per_usd_cache = None

@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret'
    with app.test_client() as client:
        with app.app_context():
            yield client

@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_success(mock_get):
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = {'rates': {'INR': 83.5}}
    mock_get.return_value = mock_response

    # Execute
    result = get_inr_per_usd()

    # Verify
    assert result == 83.5
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_exception(mock_get):
    # Setup mock to raise an exception
    mock_get.side_effect = Exception("API Error")

    # Execute
    result = get_inr_per_usd()

    # Verify
    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_invalid_json(mock_get):
    # Setup mock with invalid JSON structure missing 'rates'
    mock_response = MagicMock()
    mock_response.json.return_value = {'unexpected_key': 'value'}
    mock_get.return_value = mock_response

    # Execute
    result = get_inr_per_usd()

    # Verify
    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

@patch('app.routes.main_routes.db.session.commit')
@patch('app.routes.main_routes.db.session.delete')
@patch('app.routes.main_routes.Trades.query')
def test_delete_trade_exception(mock_query, mock_delete, mock_commit, test_client):
    # Setup mock trade
    mock_trade = MagicMock()
    mock_trade.user_id = 1
    mock_query.get_or_404.return_value = mock_trade

    # Force commit to fail
    mock_commit.side_effect = Exception("DB Commit Failed")

    with test_client.session_transaction() as sess:
        sess['user_id'] = 1

    # Execute
    response = test_client.post('/delete_trade/1')

    # Verify redirect
    assert response.status_code == 302
    assert response.location == '/home'

    # Verify flash
    with test_client.session_transaction() as sess:
        flashes = dict(sess.get('_flashes', []))
        assert flashes.get('error') == 'There was a problem to delete that trade.'
