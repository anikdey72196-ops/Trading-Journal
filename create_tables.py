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
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # SQLAlchemy 1.4+ dropped support for 'postgres://' in favor of 'postgresql://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
else:
    print("ERROR: No DATABASE_URL found in environment variables.")
    sys.exit(1)

print(f"Connecting to: {database_url.split('@')[-1]}")

# Minimal Flask app just for table creation
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
