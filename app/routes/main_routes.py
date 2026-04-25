from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db, User, Trades, DailyTarget
from form import AddTradeForm, DailyTargetForm
from datetime import date, timedelta, datetime
import requests as http_requests


main_bp = Blueprint('main', __name__)

# ------------------------- Currency Conversion -------------------------
FALLBACK_INR_PER_USD = 84.0   # used only when the live API is unreachable

def get_inr_per_usd():
    """Fetch live INR-per-USD rate from a free API. Returns a float."""
    try:
        resp = http_requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=3
        )
        data = resp.json()
        return float(data['rates']['INR'])
    except Exception:
        return FALLBACK_INR_PER_USD

def pnl_to_usd(pnl, currency, inr_per_usd):
    """Convert a PnL value to USD. If already USD, return as-is."""
    if currency == 'INR':
        return pnl / inr_per_usd
    return float(pnl)

# ------------------------- Index -------------------------
@main_bp.route('/')
@main_bp.route('/index')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.home'))
    return render_template('index.html')

# ------------------------- Home -------------------------
@main_bp.route('/home')
def home():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    user = db.session.get(User, session['user_id'])
    if not user:
        session.pop('user_id', None)
        flash('An error occurred. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    today = date.today()
    today_target = DailyTarget.query.filter_by(user_id=user.id, date=today).first()
    
    if not today_target:
        return redirect(url_for('main.set_daily_target'))

    user_trades = Trades.query.filter_by(user_id=user.id).all()

    # ---- Live INR→USD rate ----
    inr_per_usd = get_inr_per_usd()

    # ---- 7-day history (PnL converted to USD for charting) ----
    daily_history = []
    for i in range(7):
        d = today - timedelta(days=i)
        day_trades = [t for t in user_trades if t.trade_date.date() == d]
        day_pnl_usd = sum(pnl_to_usd(t.trade_pnl, getattr(t, 'profit_currency', 'USD'), inr_per_usd) for t in day_trades)
        daily_history.append({
            'date': d,
            'pnl': day_pnl_usd,
            'volume': len(day_trades)
        })
    daily_history.reverse()

    # ---- Total PnL in USD (across all history) ----
    total_pnl_usd = sum(pnl_to_usd(t.trade_pnl, getattr(t, 'profit_currency', 'USD'), inr_per_usd) for t in user_trades)

    trades_today = len([t for t in user_trades if t.trade_date.date() == today])
    remaining_trades = max(0, today_target.max_trades - trades_today)
    
    page = request.args.get('page', 1, type=int)
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    log_trades = Trades.query.filter(Trades.user_id == user.id, Trades.trade_date >= today_start, Trades.trade_date <= today_end).order_by(Trades.trade_date.desc(), Trades.id.desc()).paginate(page=page, per_page=10, error_out=False)

    return render_template(
        'home.html',
        user=user,
        trades=user_trades,
        log_trades=log_trades,
        remaining_trades=remaining_trades,
        trades_today=trades_today,
        daily_history=daily_history,
        today_target=today_target,
        total_pnl_usd=total_pnl_usd,
        inr_per_usd=inr_per_usd
    )

# ------------------------- Set Daily Target -------------------------
@main_bp.route('/set_daily_target', methods=['GET', 'POST'])
def set_daily_target():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    user = db.session.get(User, session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('auth.login'))

    today = date.today()
    if DailyTarget.query.filter_by(user_id=user.id, date=today).first():
        return redirect(url_for('main.home'))

    form = DailyTargetForm()
    if form.validate_on_submit():
        new_target = DailyTarget(user_id=user.id, date=today, max_trades=form.max_trades.data)
        try:
            db.session.add(new_target)
            db.session.commit()
            flash('Target set for today!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to set daily target. Try again.', 'danger')
            print("Database error setting daily target.")

    yesterday = today - timedelta(days=1)
    yesterday_trades = [t for t in Trades.query.filter_by(user_id=user.id).all() if t.trade_date.date() == yesterday]
    
    return render_template('set_daily_target.html', form=form, user=user, yesterday_pnl=sum(t.trade_pnl for t in yesterday_trades), yesterday_volume=len(yesterday_trades))

# ------------------------- Add Trade -------------------------
@main_bp.route('/add_trade', methods=['GET', 'POST'])
def add_trade():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    form = AddTradeForm()
    if form.validate_on_submit():
        trade = Trades(user_id=session['user_id'], trade_instruments=form.trade_instruments.data, trade_lots=form.trade_lots.data, trade_date=form.trade_date.data, trade_pnl=form.trade_pnl.data, trade_reason=form.trade_reason.data, profit_currency=form.Profit_currency.data)
        try:
            db.session.add(trade)
            db.session.commit()
            flash('Trade added successfully!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to add trade.', 'danger')
            print("Database error during trade addition.")

    return render_template('add_trade.html', form=form)

# ------------------------- Edit Trade -------------------------
@main_bp.route('/edit_trade/<int:trade_id>', methods=['GET', 'POST'])
def edit_trade(trade_id):
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    trade_to_edit = Trades.query.get_or_404(trade_id)
    if trade_to_edit.user_id != session['user_id']:
        flash("Unauthorized", "danger")
        return redirect(url_for('main.home'))
    
    form = AddTradeForm(obj=trade_to_edit)
    if form.validate_on_submit():
        trade_to_edit.trade_instruments = form.trade_instruments.data
        trade_to_edit.trade_lots = form.trade_lots.data
        trade_to_edit.trade_date = form.trade_date.data
        trade_to_edit.trade_pnl = form.trade_pnl.data
        trade_to_edit.trade_reason = form.trade_reason.data
        trade_to_edit.profit_currency = form.Profit_currency.data
        
        try:
            db.session.commit()
            flash('Trade updated!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update trade.', 'danger')
            print("Database error during trade update.")

    return render_template('edit_trade.html', form=form, trade=trade_to_edit)

# ------------------------- Delete Trade -------------------------
@main_bp.route('/delete_trade/<int:trade_id>', methods=['POST'])
def delete_trade(trade_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    trade_to_delete = Trades.query.get_or_404(trade_id)
    if trade_to_delete.user_id != session['user_id']:
        flash("Unauthorized", "danger")
        return redirect(url_for('main.home'))
    
    try:
        db.session.delete(trade_to_delete)
        db.session.commit()
        flash("Trade deleted!", "success")
    except Exception as e:
        flash("There was a problem to delete that trade.", "error")
        print("Database error during trade deletion.")
        
    return redirect(url_for('main.home'))


# -------------------------- performance log -------------------------

@main_bp.route("/performance_log")
def performance_log():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
        
    user = db.session.get(User, session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('auth.login'))
        
    user_trades = Trades.query.filter_by(user_id=user.id).order_by(Trades.trade_date.asc()).all()
    inr_per_usd = get_inr_per_usd()
    
    dates = []
    pnls_usd = []
    cumulative_pnl_usd = 0
    cumulative_pnls_usd = []
    wins = 0
    losses = 0
    setup_pnl = {}
    
    for t in user_trades:
        dates.append(t.trade_date.strftime('%b %d'))
        p_usd = pnl_to_usd(t.trade_pnl, getattr(t, 'profit_currency', 'USD'), inr_per_usd)
        pnls_usd.append(round(p_usd, 2))
        cumulative_pnl_usd += p_usd
        cumulative_pnls_usd.append(round(cumulative_pnl_usd, 2))
        
        if p_usd > 0:
            wins += 1
        elif p_usd < 0:
            losses += 1
            
        setup = t.trade_instruments.strip() if t.trade_instruments and t.trade_instruments.strip() else "Unknown"
        if len(setup) > 15:
            setup = setup[:15] + "..."
            
        setup_pnl[setup] = setup_pnl.get(setup, 0) + p_usd
        
    setup_labels = list(setup_pnl.keys())
    setup_data = [round(v, 2) for v in setup_pnl.values()]
        
    return render_template('performance_log.html', 
                           user=user, 
                           dates=dates, 
                           pnls=pnls_usd, 
                           cumulative_pnls=cumulative_pnls_usd,
                           wins=wins,
                           losses=losses,
                           setup_labels=setup_labels,
                           setup_data=setup_data)
    