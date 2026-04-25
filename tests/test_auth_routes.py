import unittest
import sys
import os

# Add app/routes to path so we can import auth_routes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'routes')))

from flask import Flask, Blueprint
from auth_routes import auth_bp
from database import db

# Dummy blueprint for 'main' to make url_for('main.home') work
main_bp = Blueprint('main', __name__)
@main_bp.route('/')
def home():
    return "Home Page"

class TestAuthRoutes(unittest.TestCase):
    def setUp(self):
        # Configure test app
        self.app = Flask(__name__, template_folder='../app/templates')
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

        # Initialize extensions
        db.init_app(self.app)

        # Register blueprints
        self.app.register_blueprint(auth_bp)
        self.app.register_blueprint(main_bp)

        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create tables
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_get(self):
        # Test GET /register loads correctly
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)

    def test_register_get_already_logged_in(self):
        # Test GET /register redirects to main.home if already logged in
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.headers['Location'])

    def test_register_post_valid(self):
        # Test successful registration
        response = self.client.post('/register', data={
            'Name': 'Test User',
            'Email': 'test@example.com',
            'Password': 'password123',
            'Avg_Daily_max_trade': 5
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        # Should redirect to login and show success message
        self.assertIn(b'Registration successful!', response.data)

        # Verify user is in database
        from database import User
        user = User.query.filter_by(Email='test@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.Name, 'Test User')
        from werkzeug.security import check_password_hash
        self.assertTrue(check_password_hash(user.Password, 'password123'))

    def test_register_post_duplicate(self):
        # Create user first
        from database import User
        from werkzeug.security import generate_password_hash
        user = User(
            Name='Existing User',
            Email='existing@example.com',
            Password=generate_password_hash('password123'),
            Daily_max_trade=5
        )
        db.session.add(user)
        db.session.commit()

        # Try registering with same email
        response = self.client.post('/register', data={
            'Name': 'New User',
            'Email': 'existing@example.com', # Duplicate email
            'Password': 'newpassword',
            'Avg_Daily_max_trade': 3
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration failed', response.data)

    def test_login_get(self):
        # Test GET /login loads correctly
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_login_get_already_logged_in(self):
        # Test GET /login redirects to main.home if already logged in
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.headers['Location'])

    def test_login_post_valid(self):
        # Create user
        from database import User
        from werkzeug.security import generate_password_hash
        user = User(
            Name='Test User',
            Email='test@example.com',
            Password=generate_password_hash('password123'),
            Daily_max_trade=5
        )
        db.session.add(user)
        db.session.commit()

        # Login
        response = self.client.post('/login', data={
            'Email': 'test@example.com',
            'Password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Check session to ensure login worked (since we redirect to the dummy Home Page and don't render flash messages)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_id'), user.id)

    def test_login_post_invalid(self):
        # Create user
        from database import User
        from werkzeug.security import generate_password_hash
        user = User(
            Name='Test User',
            Email='test@example.com',
            Password=generate_password_hash('password123'),
            Daily_max_trade=5
        )
        db.session.add(user)
        db.session.commit()

        # Login with wrong password
        response = self.client.post('/login', data={
            'Email': 'test@example.com',
            'Password': 'wrongpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password.', response.data)

        # Login with wrong email
        response = self.client.post('/login', data={
            'Email': 'wrong@example.com',
            'Password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password.', response.data)

    def test_login_post_plaintext_fallback(self):
        # Create user with plain text password
        from database import User
        user = User(
            Name='Test User',
            Email='test@example.com',
            Password='plaintextpassword',
            Daily_max_trade=5
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        # Login
        response = self.client.post('/login', data={
            'Email': 'test@example.com',
            'Password': 'plaintextpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Check session
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_id'), user_id)

        # Check database password upgraded to hash
        user_upgraded = db.session.get(User, user_id)
        from werkzeug.security import check_password_hash
        self.assertNotEqual(user_upgraded.Password, 'plaintextpassword')
        self.assertTrue(check_password_hash(user_upgraded.Password, 'plaintextpassword'))

    def test_logout(self):
        # Set session to simulate logged in user
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        # GET /logout
        response = self.client.get('/logout', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out.', response.data)

        # Verify session is empty
        with self.client.session_transaction() as sess:
            self.assertNotIn('user_id', sess)

if __name__ == '__main__':
    unittest.main()
