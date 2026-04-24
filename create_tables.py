"""
Railway release-phase script: creates all database tables.
Run via Procfile: release: python create_tables.py
This runs BEFORE gunicorn starts, with all Railway env vars already available.
"""
import sys
import os

# Make sure we can import from app/routes/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'routes'))

from flask import Flask
from database import db

# Build the DB URL from Railway env vars
database_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')

if database_url:
    if database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
else:
    mysql_host = os.environ.get('MYSQL_HOST', '').strip()
    mysql_port = os.environ.get('MYSQL_PORT', '3306').strip()
    mysql_user = os.environ.get('MYSQL_USER', '').strip()
    mysql_password = os.environ.get('MYSQL_PASSWORD', '').strip()
    mysql_db = os.environ.get('MYSQL_DATABASE', '').strip()

    if mysql_host and mysql_user and mysql_password and mysql_db:
        database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"

if not database_url:
    print("ERROR: No database URL found in environment variables.")
    print("Set MYSQL_URL, DATABASE_URL, or individual MYSQL_* variables.")
    sys.exit(1)

print(f"Connecting to: {database_url.split('@')[-1]}")

# Minimal Flask app just for table creation
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print("SUCCESS: All database tables created/verified.")
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        sys.exit(1)
