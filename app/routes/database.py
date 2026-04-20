from flask_sqlalchemy import SQLAlchemy
db=SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), unique=True, nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Daily_max_trade = db.Column(db.Integer, nullable=False)

class Trades(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trade_instruments = db.Column(db.String(80), nullable=False)
    trade_lots = db.Column(db.Integer, nullable=False)
    trade_date = db.Column(db.DateTime, nullable=False)
    trade_pnl = db.Column(db.Integer, nullable=False)
    trade_reason = db.Column(db.String(255), nullable=True)
    profit_currency = db.Column(db.String(10), nullable=False, default='USD')

class Remaining_trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    remaining_trade = db.Column(db.Integer, nullable=False)

class DailyTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    max_trades = db.Column(db.Integer, nullable=False)

class Description(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(80), nullable=False)

class Obey_rules(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    obey_rules = db.Column(db.String(80), nullable=False)

class Profit_currency(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profit_currency = db.Column(db.String(80), nullable=False)