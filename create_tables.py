"""
Render build-phase / Railway release-phase script: creates all database tables.

Render  -> set as the Build Command suffix:
           pip install -r requirements.txt && python create_tables.py
Railway -> run via Procfile: release: python create_tables.py

This runs BEFORE gunicorn starts, with all environment variables already available.
"""
import sys
import os

# Make sure we can import from app/routes/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'routes'))

from flask import Flask
from database import db

# ── Resolve the database URL ──────────────────────────────────────────────────
database_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')

if database_url:
    # Render provides 'postgresql://...' — SQLAlchemy needs psycopg2 driver prefix
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    # Old Heroku / some Render configs use 'postgres://'
    elif database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    # Railway provides 'mysql://...' — SQLAlchemy needs pymysql driver prefix
    elif database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
else:
    # Fall back to individual MYSQL_* vars (Railway local / manual config)
    mysql_host     = os.environ.get('MYSQL_HOST', '').strip()
    mysql_port     = os.environ.get('MYSQL_PORT', '3306').strip()
    mysql_user     = os.environ.get('MYSQL_USER', '').strip()
    mysql_password = os.environ.get('MYSQL_PASSWORD', '').strip()
    mysql_db       = os.environ.get('MYSQL_DATABASE', '').strip()

    if mysql_host and mysql_user and mysql_password and mysql_db:
        database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"

if not database_url:
    print("ERROR: No database URL found in environment variables.")
    print("Set DATABASE_URL (Render PostgreSQL) or MYSQL_URL / MYSQL_* vars (Railway MySQL).")
    sys.exit(1)

print(f"Connecting to: {database_url.split('@')[-1] if '@' in database_url else database_url}")

# ── Minimal Flask app just for table creation ─────────────────────────────────
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'temp-secret')
db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print("SUCCESS: All database tables created/verified.")
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        sys.exit(1)
