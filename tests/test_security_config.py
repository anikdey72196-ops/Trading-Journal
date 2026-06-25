import os
import pytest
import sys

# Add app/routes to sys.path to allow imports from it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'routes')))

def test_app_raises_error_without_secret_key(monkeypatch):
    # Ensure SECRET_KEY is not set
    monkeypatch.delenv('SECRET_KEY', raising=False)

    # Importing the app should now raise a RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        # We need to reload or carefully import since app.py might have already been loaded in other tests
        # but here it's the first time it will be loaded in this process if run in isolation.
        if 'app' in sys.modules:
            del sys.modules['app']
        import app

    assert "The SECRET_KEY environment variable is not set" in str(excinfo.value)

def test_app_starts_with_secret_key(monkeypatch):
    # Set a dummy SECRET_KEY
    monkeypatch.setenv('SECRET_KEY', 'test_secret_key')
    # Set a dummy DATABASE_URL to avoid other issues
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')

    if 'app' in sys.modules:
        del sys.modules['app']
    import app

    assert app.app.config['SECRET_KEY'] == 'test_secret_key'
