from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, EmailField, DateField, SelectMultipleField, SelectField, widgets
from wtforms.validators import DataRequired

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class Register(FlaskForm):
    Name = StringField('Name', validators=[DataRequired()], render_kw={"placeholder": "Enter your name"})
    Email = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Enter your email"})
    Password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Enter your password"})
    Avg_Daily_max_trade = IntegerField('Avg Daily Max Trades', validators=[DataRequired()], render_kw={"placeholder": "Enter your average daily max trades"})
    submit = SubmitField('Register')

class Login(FlaskForm):
    Email = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Enter your email"})
    Password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Enter your password"})
    submit = SubmitField('Login')

class AddTradeForm(FlaskForm):
    trade_instruments = StringField('Trade Instruments', validators=[DataRequired()], render_kw={"placeholder": "e.g. NIFTY, BANKNIFTY"})
    trade_lots = IntegerField('Trade Lots', validators=[DataRequired()], render_kw={"placeholder": "e.g. 1"})
    trade_date = DateField('Trade Date', validators=[DataRequired()])
    trade_pnl = IntegerField('Trade PnL', validators=[DataRequired()], render_kw={"placeholder": "e.g. 500 or -200"})
    trade_reason = StringField('Trade Reason / Notes', render_kw={"placeholder": "e.g. respect the Support zone, Liquidity... (Optional)"})
    Profit_currency = SelectField('Profit Currency', choices=[('INR', 'INR'), ('USD', 'USD')], validators=[DataRequired()])
    Rules = MultiCheckboxField('Rules', choices=[
        ('fixed_sl', 'Fixed Stop loss'),
        ('no_overtrading', 'No over trading'),
        ('follow_rrr', 'Follow Risk Reward Ratio'),
        ('no_revenge', 'No revenge trading'),
        ('quality', 'Based on quality not quantity'),
        ('strict_risk', 'Risked exactly 1% (or less) of account balance'),
        ('no_fomo', 'Did not force a trade (No FOMO)')
    ])
    submit = SubmitField('Submit Trade')

class DailyTargetForm(FlaskForm):
    max_trades = IntegerField('Daily Target (Max Trades)', validators=[DataRequired()], render_kw={"placeholder": "e.g. 5"})
    submit = SubmitField('Set Target')