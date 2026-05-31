import timeit

setup_code = '''
from datetime import date, timedelta, datetime

class Trade:
    def __init__(self, d, pnl, c):
        self.trade_date = datetime.combine(d, datetime.min.time())
        self.trade_pnl = pnl
        self.profit_currency = c

today = date.today()
recent_trades = []
for i in range(7):
    d = today - timedelta(days=i)
    for _ in range(100):
        recent_trades.append(Trade(d, 10.0, 'USD'))

def pnl_to_usd(pnl, currency, rate):
    return pnl
inr_per_usd = 84.0
'''

test_code_old = '''
daily_history = []
for i in range(7):
    d = today - timedelta(days=i)
    day_trades = [t for t in recent_trades if t.trade_date.date() == d]
    day_pnl_usd = sum(pnl_to_usd(t.trade_pnl, getattr(t, 'profit_currency', 'USD'), inr_per_usd) for t in day_trades)
    daily_history.append({
        'date': d,
        'pnl': day_pnl_usd,
        'volume': len(day_trades)
    })
daily_history.reverse()
trades_today = len([t for t in recent_trades if t.trade_date.date() == today])
'''

test_code_new = '''
from collections import defaultdict
grouped_trades = defaultdict(list)
for t in recent_trades:
    grouped_trades[t.trade_date.date()].append(t)

daily_history = []
for i in range(7):
    d = today - timedelta(days=i)
    day_trades = grouped_trades.get(d, [])
    day_pnl_usd = sum(pnl_to_usd(t.trade_pnl, getattr(t, 'profit_currency', 'USD'), inr_per_usd) for t in day_trades)
    daily_history.append({
        'date': d,
        'pnl': day_pnl_usd,
        'volume': len(day_trades)
    })
daily_history.reverse()
trades_today = len(grouped_trades.get(today, []))
'''

time_old = timeit.timeit(test_code_old, setup=setup_code, number=1000)
time_new = timeit.timeit(test_code_new, setup=setup_code, number=1000)

print(f"Old approach: {time_old:.5f}s")
print(f"New approach: {time_new:.5f}s")
print(f"Improvement: {((time_old - time_new) / time_old) * 100:.2f}%")
