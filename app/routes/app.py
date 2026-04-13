
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from form import Register, Login, AddTradeForm, DailyTargetForm
from database import db, User, Trades, DailyTarget
from datetime import date, timedelta


app = Flask(__name__, template_folder='templets')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading_journal.db'
app.config['SECRET_KEY'] = 'a_very_secret_and_complex_key'

csrf = CSRFProtect(app)

db.init_app(app)


@app.route('/')
@app.route('/index')
def index():
    """Public landing page or marketing page."""

    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    
    if 'user_id' in session:
        return redirect(url_for('home'))

    form = Register()
    if form.validate_on_submit():
        
        user = User(
            Name=form.Name.data,
            Email=form.Email.data,
            Password=form.Password.data, 
            Daily_max_trade=form.Daily_max_trade.data
        )
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Email or Username might already exist.', 'danger')
            print(f"Database error during registration: {e}")

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    # If a user is already logged in, redirect them to their home/dashboard
    if 'user_id' in session:
        return redirect(url_for('home'))

    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(Email=form.Email.data).first()
        
        
        if user and user.Password == form.Password.data: 
           
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """User logout route."""
    # Clear the session data
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



@app.route('/home')
def home():
    """
    User dashboard (the primary page after logging in).
    Only accessible by logged-in users.
    """
   
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    
    user = db.session.get(User, session['user_id'])
    
    
    if not user:
        session.pop('user_id', None)
        flash('An error occurred. Please log in again.', 'danger')
        return redirect(url_for('login'))

    today = date.today()
    # Check for today's DailyTarget
    today_target = DailyTarget.query.filter_by(user_id=user.id, date=today).first()
    
    # If no target set for today, enforce setting it
    if not today_target:
        return redirect(url_for('set_daily_target'))

    # All trades for this user
    user_trades = Trades.query.filter_by(user_id=user.id).all()

    # Calculate last 7 days history
    daily_history = []
    for i in range(7):
        d = today - timedelta(days=i)
        
        # Filter trades for this specific day
        day_trades = [t for t in user_trades if t.trade_date.date() == d]
        day_pnl = sum(t.trade_pnl for t in day_trades)
        day_volume = len(day_trades)
        
        daily_history.append({
            'date': d,
            'pnl': day_pnl,
            'volume': day_volume
        })
    
    # Reverse so it shows chronologically (oldest of the 7 days on the left/first)
    daily_history.reverse()

    # Count today's trades to compute remaining trades from dynamic today_target
    trades_today = len([t for t in user_trades if t.trade_date.date() == today])
    remaining_trades = max(0, today_target.max_trades - trades_today)

    return render_template(
        'home.html',
        user=user,
        trades=user_trades,
        remaining_trades=remaining_trades,
        trades_today=trades_today,
        daily_history=daily_history,
        today_target=today_target
    )

@app.route('/set_daily_target', methods=['GET', 'POST'])
def set_daily_target():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))

    today = date.today()
    existing_target = DailyTarget.query.filter_by(user_id=user.id, date=today).first()
    if existing_target:
        return redirect(url_for('home'))

    form = DailyTargetForm()
    if form.validate_on_submit():
        new_target = DailyTarget(
            user_id=user.id,
            date=today,
            max_trades=form.max_trades.data
        )
        try:
            db.session.add(new_target)
            db.session.commit()
            flash('Target set for today! Let\'s crush it!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to set daily target. Try again.', 'danger')
            print(f"Database error setting daily target: {e}")

    yesterday = today - timedelta(days=1)
    yesterday_trades = Trades.query.filter_by(user_id=user.id).all()
    yesterday_trades = [t for t in yesterday_trades if t.trade_date.date() == yesterday]
    yesterday_pnl = sum(t.trade_pnl for t in yesterday_trades)
    yesterday_volume = len(yesterday_trades)

    return render_template('set_daily_target.html', form=form, user=user, yesterday_pnl=yesterday_pnl, yesterday_volume=yesterday_volume)

@app.route('/add_trade', methods=['GET', 'POST'])
def add_trade():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    form = AddTradeForm()
    if form.validate_on_submit():
        trade = Trades(
            user_id=session['user_id'],
            trade_instruments=form.trade_instruments.data,
            trade_lots=form.trade_lots.data,
            trade_date=form.trade_date.data,
            trade_pnl=form.trade_pnl.data
        )
        try:
            db.session.add(trade)
            db.session.commit()
            flash('Trade added successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to add trade.', 'danger')
            print(f"Database error during trade addition: {e}")

    return render_template('add_trade.html', form=form)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)

