import unittest
import sys
import os

# Add app/routes to path so we can import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'routes')))
from utils import pnl_to_usd

class TestUtils(unittest.TestCase):
    def test_pnl_to_usd_inr(self):
        # Case: INR to USD conversion
        # 840 INR / 84.0 INR/USD = 10.0 USD
        self.assertEqual(pnl_to_usd(840, 'INR', 84.0), 10.0)
        self.assertEqual(pnl_to_usd(0, 'INR', 84.0), 0.0)
        self.assertEqual(pnl_to_usd(-84, 'INR', 84.0), -1.0)

    def test_pnl_to_usd_usd(self):
        # Case: Already USD
        self.assertEqual(pnl_to_usd(10.0, 'USD', 84.0), 10.0)
        self.assertEqual(pnl_to_usd(10, 'USD', 84.0), 10.0)
        self.assertEqual(pnl_to_usd(-5.5, 'USD', 84.0), -5.5)

    def test_pnl_to_usd_other_currency(self):
        # Case: Other currency should be treated like USD (returning float)
        self.assertEqual(pnl_to_usd(100, 'EUR', 84.0), 100.0)

    def test_pnl_to_usd_floats(self):
        # Case: Float inputs
        self.assertAlmostEqual(pnl_to_usd(100.0, 'INR', 80.0), 1.25)
        self.assertEqual(pnl_to_usd(12.34, 'USD', 84.0), 12.34)

if __name__ == '__main__':
    unittest.main()
