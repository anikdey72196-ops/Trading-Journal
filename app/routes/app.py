from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from database import db

import os
from dotenv import load_dotenv

# Import our new Blueprints
from auth_routes import auth_bp
from main_routes import main_bp

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
root_dir = os.path.abspath(os.path.join(base_dir, '..'))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'),
            instance_path=os.path.join(root_dir, 'instance'))

# Load environment variables from app/.env
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

# Build the database URL from environment variables
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # SQLAlchemy 1.4+ dropped support for 'postgres://' in favor of 'postgresql://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
else:
    # Fall back to SQLite (local dev only)
    print("WARNING: No DATABASE_URL configured. Falling back to local SQLite.")
    database_url = 'sqlite:///' + os.path.join(app.instance_path, 'trading_journal.db')

print(f"Using database: {database_url.split('@')[-1] if '@' in database_url else database_url}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_fallback_secret')

# Tell Flask to trust Railway's reverse proxy (fixes HTTPS/session issues)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

csrf = CSRFProtect(app)
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

# Create all DB tables on startup — wrapped in try/except so a slow DB
# connection at boot time doesn't crash the entire gunicorn process
with app.app_context():
    try:
        db.create_all()
        print("Database tables created/verified successfully.")
    except Exception as e:
        print(f"WARNING: Could not create DB tables at startup: {e}")
        print(f"DB URI used: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')}")

if __name__ == '__main__':
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)
    app.run(debug=True)
