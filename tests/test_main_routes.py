import pytest
from unittest.mock import patch, MagicMock
from app.routes.main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD

@pytest.fixture(autouse=True)
def reset_cache():
    from app.routes import main_routes
    main_routes._inr_per_usd_cache = None
    main_routes._inr_per_usd_cache_time = 0

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

def test_add_trade_error_path():
    from flask import Flask
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.database import db
    import datetime

    test_app = Flask(__name__, template_folder='../app/templates')
    test_app.config['TESTING'] = True
    test_app.config['SECRET_KEY'] = 'test'
    test_app.config['WTF_CSRF_ENABLED'] = False
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    db.init_app(test_app)
    test_app.register_blueprint(main_bp)
    test_app.register_blueprint(auth_bp)

    with test_app.app_context():
        # Setup db structure with memory to satisfy blueprint setup
        db.create_all()

        with patch('app.routes.main_routes.DailyTarget.query') as mock_target_query, \
             patch('app.routes.main_routes.Trades.query') as mock_trades_query, \
             patch('app.routes.main_routes.db.session.add') as mock_add, \
             patch('app.routes.main_routes.db.session.commit') as mock_commit, \
             patch('app.routes.main_routes.db.session.rollback') as mock_rollback:

            # Use test app context for the request
            with test_app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = 1

                # Submit the trade
                data = {
                    'trade_date': datetime.date.today().strftime('%Y-%m-%d'),
                    'trade_instruments': 'AAPL',
                    'trade_lots': '1',
                    'trade_pnl': '10',
                    'trade_reason': 'Test',
                    'Profit_currency': 'USD'
                }

                mock_target = MagicMock()
                mock_target.max_trades = 5

                # Set mocks to trigger the exception
                mock_target_query.filter_by.return_value.first.return_value = mock_target
                mock_trades_query.filter.return_value.count.return_value = 0
                mock_commit.side_effect = Exception("Mock DB error")

                response = client.post('/add_trade', data=data, follow_redirects=True)


                # Should render the template with a flash message
                assert b'Failed to add trade.' in response.data
                mock_rollback.assert_called_once()
