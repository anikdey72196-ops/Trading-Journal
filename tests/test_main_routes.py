import unittest
import sys
import os
from flask import Flask, session

# Add app/routes to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'routes')))

import main_routes
import auth_routes

class TestIndex(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder='../app/templates')
        self.app.secret_key = 'test_secret'
        self.app.register_blueprint(main_routes.main_bp)
        self.app.register_blueprint(auth_routes.auth_bp)
        self.client = self.app.test_client()

    def test_index_route_no_user(self):
        """Test GET / returns 200 when no user is in the session."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_index_alt_route_no_user(self):
        """Test GET /index returns 200 when no user is in the session."""
        response = self.client.get('/index')
        self.assertEqual(response.status_code, 200)

    def test_index_route_with_user(self):
        """Test GET / redirects to /home when user is in the session."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/home')

    def test_index_alt_route_with_user(self):
        """Test GET /index redirects to /home when user is in the session."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        response = self.client.get('/index')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/home')

if __name__ == '__main__':
    unittest.main()
