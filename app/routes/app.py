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
# Railway sets individual MYSQL_* vars; it may also set DATABASE_URL or MYSQL_URL
database_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')

if not database_url:
    # Try to build the URL from individual MYSQL_* vars (how Railway exposes them)
    mysql_host = os.environ.get('MYSQL_HOST', '').strip()
    mysql_port = os.environ.get('MYSQL_PORT', '3306').strip()
    mysql_user = os.environ.get('MYSQL_USER', '').strip()
    mysql_password = os.environ.get('MYSQL_PASSWORD', '').strip()
    mysql_db = os.environ.get('MYSQL_DATABASE', '').strip()

    if mysql_host and mysql_user and mysql_password and mysql_db:
        database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"

# If still no valid URL (i.e., running locally without a DB), fall back to SQLite
if not database_url:
    print("WARNING: No database URL configured. Falling back to local SQLite.")
    database_url = 'sqlite:///' + os.path.join(app.instance_path, 'trading_journal.db')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
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
    print("Database tables created/verified successfully.")

# print(f"WARNING: Could not create DB tables at startup: {e}")
# print(f"   DB URI used: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')}")

if __name__ == '__main__':
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)
    app.run(debug=True)
