from functools import wraps
from flask import session, flash, redirect, url_for

def pnl_to_usd(pnl, currency, inr_per_usd):
    """Convert a PnL value to USD. If already USD, return as-is."""
    if currency == 'INR':
        return pnl / inr_per_usd
    return float(pnl)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
