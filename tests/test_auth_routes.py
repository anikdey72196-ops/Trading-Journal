import unittest
from unittest.mock import patch, MagicMock

# Important: do not use sys.path.insert, tests should be run with PYTHONPATH=.
from app.routes.app import app

class TestAuthRoutes(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['WTF_CSRF_CHECK_DEFAULT'] = False
        self.client = app.test_client()

    @patch('app.routes.auth_routes.User')
    def test_login_get(self, mock_user):
        with app.app_context():
            response = self.client.get('/login')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Login', response.data)

    @patch('auth_routes.User')
    @patch('auth_routes.check_password_hash')
    def test_login_post_success(self, mock_check_pw, mock_user):
        mock_check_pw.return_value = True

        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user_instance.Password = 'hashed_pw'

        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance

        with app.test_client() as client:
            with app.app_context():
                response = client.post('/login', data=dict(
                    Email='test@example.com',
                    Password='password123'
                ), follow_redirects=False)

                self.assertEqual(response.status_code, 302)

                with client.session_transaction() as sess:
                    self.assertEqual(sess.get('user_id'), 1)

    @patch('auth_routes.User')
    def test_login_post_invalid_email(self, mock_user):
        mock_user.query.filter_by.return_value.first.return_value = None

        with app.test_client() as client:
            with app.app_context():
                response = client.post('/login', data=dict(
                    Email='wrong@example.com',
                    Password='password123'
                ), follow_redirects=True)

                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Invalid email or password.', response.data)

                with client.session_transaction() as sess:
                    self.assertNotIn('user_id', sess)

    @patch('auth_routes.User')
    @patch('auth_routes.check_password_hash')
    def test_login_post_invalid_password(self, mock_check_pw, mock_user):
        mock_check_pw.return_value = False

        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user_instance.Password = 'hashed_pw'

        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance

        with app.test_client() as client:
            with app.app_context():
                response = client.post('/login', data=dict(
                    Email='test@example.com',
                    Password='wrongpassword'
                ), follow_redirects=True)

                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Invalid email or password.', response.data)

                with client.session_transaction() as sess:
                    self.assertNotIn('user_id', sess)

    def test_login_already_logged_in(self):
        with app.test_client() as client:
            with app.app_context():
                with client.session_transaction() as sess:
                    sess['user_id'] = 1

                response = client.get('/login', follow_redirects=False)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.location.endswith('/home') or response.location == '/home')

if __name__ == '__main__':
    unittest.main()
