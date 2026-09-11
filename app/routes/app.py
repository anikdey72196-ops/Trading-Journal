import secrets
from flask import Flask, flash, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix
from database import db

import os
from dotenv import load_dotenv

# Import Blueprints
from auth_routes import auth_bp
from main_routes import main_bp

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
root_dir = os.path.abspath(os.path.join(base_dir, '..'))

os.makedirs(os.path.join(root_dir, "instance"), exist_ok=True)
app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'),
            instance_path=os.path.join(root_dir, 'instance'))

# Load environment variables from app/.env (local dev only)
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
#
# MODE: LOCAL SQLITE  (active for local testing — no external DB needed)
# SQLAlchemy creates trading_journal.db automatically inside the /instance folder.
#
os.makedirs(app.instance_path, exist_ok=True)
database_url = 'sqlite:///' + os.path.join(app.instance_path, 'trading_journal.db')
print(f"[DB] Using local SQLite: {database_url}")

# ─────────────────────────────────────────────────────────────────────────────
# COMMENTED OUT: Render (PostgreSQL) + Railway (MySQL) remote DB config.
# Uncomment the block below and comment out the SQLite block above when deploying.
# ─────────────────────────────────────────────────────────────────────────────
# load_dotenv(env_path)
# database_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
#
# if database_url:
#     # Render: 'postgresql://' -> 'postgresql+psycopg2://'
#     if database_url.startswith('postgresql://'):
#         database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
#     # Old Render/Heroku: 'postgres://' -> 'postgresql+psycopg2://'
#     elif database_url.startswith('postgres://'):
#         database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
#     # Railway: 'mysql://' -> 'mysql+pymysql://'
#     elif database_url.startswith('mysql://'):
#         database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
# else:
#     # Railway individual MYSQL_* env vars fallback
#     mysql_host     = os.environ.get('MYSQL_HOST', '').strip()
#     mysql_port     = os.environ.get('MYSQL_PORT', '3306').strip()
#     mysql_user     = os.environ.get('MYSQL_USER', '').strip()
#     mysql_password = os.environ.get('MYSQL_PASSWORD', '').strip()
#     mysql_db       = os.environ.get('MYSQL_DATABASE', '').strip()
#     if mysql_host and mysql_user and mysql_password and mysql_db:
#         database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
#
# if not database_url:
#     print("WARNING: No remote DB URL found. Falling back to SQLite.")
#     database_url = 'sqlite:///' + os.path.join(app.instance_path, 'trading_journal.db')
# ─────────────────────────────────────────────────────────────────────────────

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Consistent, persistent SECRET_KEY to prevent CSRF tokens from invalidating on server restart
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tradelytics-permanent-secret-key-2026-9f8a7b6c5d4e3f2a1')
app.config['WTF_CSRF_TIME_LIMIT'] = 86400  # 24 hours

# Trust reverse proxy headers (Render / Railway / Nginx)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

csrf = CSRFProtect(app)
db.init_app(app)

# Graceful CSRF Error Handler: instead of a raw 400 crash page, redirect with a friendly message
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash("Your session expired or the form timed out. Please try logging in again.", "warning")
    return redirect(request.referrer or url_for('auth.login'))

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

@app.context_processor
def inject_global_vars():
    from database import DailyTarget, Trades
    from flask import session
    from datetime import date
    if 'user_id' in session:
        today = date.today()
        today_target = DailyTarget.query.filter_by(user_id=session['user_id'], date=today).first()
        trades_today_count = Trades.query.filter(
            Trades.user_id == session['user_id'],
            db.func.date(Trades.trade_date) == today
        ).count()
        remaining_trades = max(0, today_target.max_trades - trades_today_count) if today_target else 10
        return dict(remaining_trades=remaining_trades)
    return dict(remaining_trades=10)

# Auto-create all DB tables on startup
with app.app_context():
    try:
        db.create_all()
        print("[DB] Tables created/verified successfully.")
    except Exception as e:
        print(f"[DB] WARNING: Could not create tables at startup: {e}")
        print(f"DB URI used: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)