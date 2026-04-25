import unittest
from unittest.mock import patch, Mock
import sys
import os

# Add app/routes to path so we can import main_routes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'routes')))
import main_routes

class TestMainRoutes(unittest.TestCase):
    @patch('main_routes.http_requests.get')
    def test_get_inr_per_usd_success(self, mock_get):
        # Mock successful response
        mock_resp = Mock()
        mock_resp.json.return_value = {
            'rates': {
                'INR': 83.5
            }
        }
        mock_get.return_value = mock_resp

        result = main_routes.get_inr_per_usd()

        self.assertEqual(result, 83.5)
        mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

    @patch('main_routes.http_requests.get')
    def test_get_inr_per_usd_network_error(self, mock_get):
        # Mock network error
        mock_get.side_effect = Exception("Connection timeout")

        result = main_routes.get_inr_per_usd()

        self.assertEqual(result, main_routes.FALLBACK_INR_PER_USD)
        mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

    @patch('main_routes.http_requests.get')
    def test_get_inr_per_usd_invalid_data(self, mock_get):
        # Mock response with missing 'INR' key
        mock_resp = Mock()
        mock_resp.json.return_value = {
            'rates': {
                'EUR': 0.92
            }
        }
        mock_get.return_value = mock_resp

        result = main_routes.get_inr_per_usd()

        self.assertEqual(result, main_routes.FALLBACK_INR_PER_USD)
        mock_get.assert_called_once_with('https://api.exchangerate-api.com/v4/latest/USD', timeout=3)

if __name__ == '__main__':
    unittest.main()
