import time
from datetime import date, timedelta, datetime
import sys
import os

# add to path
sys.path.append(os.path.abspath("app/routes"))

# Set up the app context
from app import app
from database import db, User, Trades

with app.app_context():
    # Setup test data
    db.create_all()
    user = User.query.filter_by(Name='benchmark_user').first()
    if not user:
        user = User(Name='benchmark_user', Email='bench@example.com', Password='pwd', Daily_max_trade=10)
        db.session.add(user)
        db.session.commit()

    # Check if we have trades
    if Trades.query.filter_by(user_id=user.id).count() < 10000:
        print("Inserting test trades...")
        yesterday = date.today() - timedelta(days=1)
        trades_to_add = []
        for i in range(10000):
            # 9000 trades today, 1000 yesterday
            trade_date = datetime.now() if i < 9000 else datetime.combine(yesterday, datetime.min.time())
            trades_to_add.append(Trades(user_id=user.id, trade_instruments='EURUSD', trade_lots=1, trade_date=trade_date, trade_pnl=10, profit_currency='USD'))
        db.session.bulk_save_objects(trades_to_add)
        db.session.commit()

    print("Running benchmark...")
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Old method
    start = time.time()
    for _ in range(10):
        yesterday_trades = [t for t in Trades.query.filter_by(user_id=user.id).all() if t.trade_date.date() == yesterday]
    old_time = time.time() - start
    print(f"Old method (10 runs): {old_time:.4f}s")

    # New method
    from sqlalchemy import func
    start = time.time()
    for _ in range(10):
        # We might need cast or func.date depending on dialect, let's try func.date
        yesterday_trades_new = Trades.query.filter(Trades.user_id == user.id, func.date(Trades.trade_date) == yesterday).all()
    new_time = time.time() - start
    print(f"New method (10 runs): {new_time:.4f}s")

    # Verify correctness
    print(f"Old result size: {len(yesterday_trades)}")
    print(f"New result size: {len(yesterday_trades_new)}")
    assert len(yesterday_trades) == len(yesterday_trades_new)
