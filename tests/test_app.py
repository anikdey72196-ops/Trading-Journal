import unittest
import os
import sys

# Ensure app/routes is in path so app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/routes')))

from app import app

class TestAppConfig(unittest.TestCase):
    def test_secure_cookies(self):
        # Verify that the secure cookie configurations are set correctly
        self.assertTrue(app.config.get('SESSION_COOKIE_SECURE'), "SESSION_COOKIE_SECURE should be True")
        self.assertTrue(app.config.get('SESSION_COOKIE_HTTPONLY'), "SESSION_COOKIE_HTTPONLY should be True")

if __name__ == "__main__":
    unittest.main()
