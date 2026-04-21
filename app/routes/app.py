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

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///trading_journal.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_fallback_secret')

# Tell Flask to trust Railway's reverse proxy (fixes HTTPS/session issues)
# x_for=1 means 1 proxy is in front of us (Railway's load balancer)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

csrf = CSRFProtect(app)
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

# Create all DB tables on startup (runs under both gunicorn and python app.py)

with app.app_context():
    db.create_all()
    print("✅ Database tables created/verified successfully.")

# print(f"⚠️  WARNING: Could not create DB tables at startup: {e}")
# print(f"   DB URI used: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')}")

if __name__ == '__main__':
    app.run(debug=True)
