def pnl_to_usd(pnl, currency, inr_per_usd):
    """Convert a PnL value to USD. If already USD, return as-is."""
    if currency == 'INR':
        return pnl / inr_per_usd
    return float(pnl)
