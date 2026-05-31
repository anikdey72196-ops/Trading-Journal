import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure app/routes is in path so main_routes can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/routes')))

from main_routes import get_inr_per_usd, FALLBACK_INR_PER_USD
import main_routes

@patch('main_routes.http_requests.get')
def test_get_inr_per_usd_success(mock_get):
    # Reset cache to avoid cross-test pollution
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

@patch('main_routes.http_requests.get')
def test_get_inr_per_usd_exception(mock_get):
    # Reset cache to avoid cross-test pollution
    main_routes._inr_per_usd_cache = None

    # Setup mock to raise an exception
    mock_get.side_effect = Exception("API Error")

    # Execute
    result = get_inr_per_usd()

    # Verify
    assert result == FALLBACK_INR_PER_USD
    mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

@patch('main_routes.http_requests.get')
def test_get_inr_per_usd_invalid_json(mock_get):
    # Reset cache to avoid cross-test pollution
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
