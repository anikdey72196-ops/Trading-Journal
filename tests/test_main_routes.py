import pytest
from unittest.mock import patch, MagicMock
from app.routes.main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD

@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_success(mock_get):
    from app.routes import main_routes
    main_routes._inr_per_usd_cache = None

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
    from app.routes import main_routes
    main_routes._inr_per_usd_cache = None

    # Setup mock to raise an exception
    mock_get.side_effect = Exception("API Error")

    # Execute
    result = get_inr_per_usd()

    # Verify
    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

@patch('app.routes.main_routes.http_requests.get')
def test_get_inr_per_usd_invalid_json(mock_get):
    from app.routes import main_routes
    main_routes._inr_per_usd_cache = None

    # Setup mock with invalid JSON structure missing 'rates'
    mock_response = MagicMock()
    mock_response.json.return_value = {'unexpected_key': 'value'}
    mock_get.return_value = mock_response

    # Execute
    result = get_inr_per_usd()

    # Verify
    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)
