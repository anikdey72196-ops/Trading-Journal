import pytest
from unittest.mock import patch, MagicMock
from app.routes.main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD
import app.routes.main_routes

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
    app.routes.main_routes._inr_per_usd_cache = None
    app.routes.main_routes._cache_timestamp = 0

    # Setup mock to raise an exception
    mock_get.side_effect = Exception("API Error")

    # Execute
    result = get_inr_per_usd()

    # Verify
    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_invalid_json(mock_get):
    app.routes.main_routes._inr_per_usd_cache = None
    app.routes.main_routes._cache_timestamp = 0

    # Setup mock with invalid JSON structure missing 'rates'
    mock_response = MagicMock()
    mock_response.json.return_value = {'unexpected_key': 'value'}
    mock_get.return_value = mock_response

    # Execute
    result = get_inr_per_usd()

    # Verify
    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

def test_add_trade_daily_limit_reached():
    from app.routes.app import app
    from unittest.mock import patch, MagicMock

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = 1

            with patch('app.routes.main_routes.DailyTarget.query') as mock_dt_query, \
                 patch('app.routes.main_routes.Trades.query') as mock_tr_query:

                # Setup mock for DailyTarget (max 1 trade)
                mock_target = MagicMock()
                mock_target.max_trades = 1
                mock_dt_query.filter_by.return_value.first.return_value = mock_target

                # Setup mock for Trades (already 1 trade today)
                mock_tr_query.filter.return_value.count.return_value = 1

                response = client.post('/add_trade', data={
                    'trade_instruments': 'GBPUSD',
                    'trade_lots': '1.0',
                    'trade_date': '2023-10-27',
                    'trade_pnl': '20.0',
                    'trade_reason': 'Test2',
                    'Profit_currency': 'USD'
                }, follow_redirects=False)

                assert response.status_code == 302
                assert response.location == '/home'

                with client.session_transaction() as sess:
                    assert ('danger', 'Daily trade limit reached! You cannot add more trades today.') in sess['_flashes']
