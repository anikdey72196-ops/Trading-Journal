import unittest
from werkzeug.datastructures import MultiDict
from flask import Flask
from app.routes.form import Register

class TestFormPasswordValidation(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SECRET_KEY'] = 'test-secret'
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_weak_password_rejected_length(self):
        form = Register(formdata=MultiDict({
            'Name': 'Test User',
            'Email': 'test@example.com',
            'Password': 'short1',
            'Avg_Daily_max_trade': '5'
        }))
        self.assertFalse(form.validate())
        self.assertIn('Password', form.errors)
        self.assertIn('Password must be at least 8 characters long.', form.errors['Password'])

    def test_weak_password_rejected_complexity_no_number(self):
        form = Register(formdata=MultiDict({
            'Name': 'Test User',
            'Email': 'test@example.com',
            'Password': 'passwordonly',
            'Avg_Daily_max_trade': '5'
        }))
        self.assertFalse(form.validate())
        self.assertIn('Password', form.errors)
        self.assertIn('Password must contain at least one letter and one number.', form.errors['Password'])

    def test_weak_password_rejected_complexity_no_letter(self):
        form = Register(formdata=MultiDict({
            'Name': 'Test User',
            'Email': 'test@example.com',
            'Password': '1234567890',
            'Avg_Daily_max_trade': '5'
        }))
        self.assertFalse(form.validate())
        self.assertIn('Password', form.errors)
        self.assertIn('Password must contain at least one letter and one number.', form.errors['Password'])

    def test_strong_password_accepted(self):
        form = Register(formdata=MultiDict({
            'Name': 'Test User',
            'Email': 'test@example.com',
            'Password': 'StrongPassword123!',
            'Avg_Daily_max_trade': '5'
        }))
        self.assertTrue(form.validate())
        self.assertNotIn('Password', form.errors)

if __name__ == '__main__':
    unittest.main()
