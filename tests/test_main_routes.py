import pytest
from unittest.mock import patch, MagicMock
from app.routes.main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD
from datetime import datetime
import os
import sys

# Ensure proper path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/routes')))

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
    import app.routes.main_routes as mr
    mr._inr_per_usd_cache = None
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
    import app.routes.main_routes as mr
    mr._inr_per_usd_cache = None
    result = get_inr_per_usd()

    # Verify
    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)


@pytest.fixture
def test_app():
    from flask import Flask
    app = Flask(__name__, template_folder='../app/templates')
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test_secret',
    })

    from app.routes.main_routes import main_bp
    app.register_blueprint(main_bp)

    return app

@pytest.fixture
def client(test_app):
    return test_app.test_client()

def test_edit_trade_database_error(test_app, client):
    with test_app.app_context():
        # Setup mock trade
        mock_trade = MagicMock()
        mock_trade.user_id = 1

        # We need to mock these inside the app context
        with patch('app.routes.main_routes.db.session.rollback') as mock_rollback, \
             patch('app.routes.main_routes.db.session.commit') as mock_commit, \
             patch('app.routes.main_routes.AddTradeForm') as mock_form_class, \
             patch('app.routes.main_routes.Trades') as mock_trades:

            # Setup mock get_or_404
            mock_trades.query.get_or_404.return_value = mock_trade

            # Setup mock form validation
            mock_form_instance = MagicMock()
            mock_form_instance.validate_on_submit.return_value = True
            mock_form_instance.trade_instruments.data = 'MSFT'
            mock_form_instance.trade_lots.data = 2.0
            mock_form_instance.trade_date.data = datetime.now()
            mock_form_instance.trade_pnl.data = 200.0
            mock_form_instance.trade_reason.data = 'Updated reason'
            mock_form_instance.Profit_currency.data = 'USD'
            mock_form_class.return_value = mock_form_instance

            # Setup mock commit to raise Exception
            mock_commit.side_effect = Exception("Database error!")

            with client.session_transaction() as sess:
                sess['user_id'] = 1

            response = client.post(
                '/edit_trade/1',
                data={},
                follow_redirects=True
            )

            # Check that error message is in the response body indicating flash worked
            assert b'Failed to update trade.' in response.data

            # Verify rollback was called
            mock_rollback.assert_called_once()

            # Verify the mocked commit was called
            mock_commit.assert_called_once()
