import pandas as pd
import numpy as np
import numpy_financial as npf
from scipy.optimize import newton

def calculate_aum(client_id, db):
    """Calculate Total Assets Under Management for a client."""
    query = '''
        SELECT t.units, s.current_nav
        FROM transactions t
        JOIN folios f ON t.folio_id = f.folio_id
        JOIN schemes s ON t.scheme_id = s.scheme_id
        WHERE f.client_id = ?
    '''
    df = db.run_query(query, params=(client_id,))
    if df.empty:
        return 0.0
    
    # Simple sum of (units * current_nav) across all transactions
    # Note: This assumes current holdings = sum of all transaction units (Buys positive, Sells negative)
    df['value'] = df['units'] * df['current_nav']
    return float(df['value'].sum())

def xirr(cashflows, dates):
    """Calculate XIRR for a sequence of cashflows and dates."""
    def xnpv(rate, cashflows, dates):
        d0 = dates[0]
        return sum([cf / (1 + rate)**((d - d0).days / 365.25) for cf, d in zip(cashflows, dates)])

    try:
        return newton(lambda r: xnpv(r, cashflows, dates), 0.1)
    except (RuntimeError, OverflowError):
        return None

def calculate_client_metrics(client_id, db):
    """Calculate comprehensive metrics for a client."""
    # 1. Fetch Transactions
    query = '''
        SELECT t.date, t.amount, t.type, t.units, s.current_nav
        FROM transactions t
        JOIN folios f ON t.folio_id = f.folio_id
        JOIN schemes s ON t.scheme_id = s.scheme_id
        WHERE f.client_id = ?
    '''
    df = db.run_query(query, params=(client_id,))
    if df.empty:
        return {"aum": 0.0, "net_investment": 0.0, "total_gain": 0.0, "xirr": 0.0}

    df['date'] = pd.to_datetime(df['date'])
    
    # 2. AUM
    current_value = float((df['units'] * df['current_nav']).sum())
    
    # 3. Net Investment
    # Purchases are positive amounts in DB, Redemptions should be treated as outflows
    # For AUM/Gains, Net Investment = Total Invested - Total Withdrawn
    invested = df[df['type'].isin(['PURCHASE', 'SIP'])]['amount'].sum()
    withdrawn = df[df['type'].isin(['REDEMPTION', 'SWP'])]['amount'].sum()
    net_investment = float(invested - withdrawn)
    
    # 4. Total Gain
    total_gain = current_value - net_investment
    
    # 5. XIRR Preparation
    # Cashflows: Investments are negative (money going out), Redemptions are positive (money coming in)
    # Final value is a positive cashflow today
    cashflows = []
    dates = []
    
    for _, row in df.iterrows():
        # If Purchase/SIP -> Money flows OUT of pocket (-ve)
        if row['type'] in ['PURCHASE', 'SIP']:
            cashflows.append(-row['amount'])
        # If Redemption/SWP -> Money flows IN (+ve)
        else:
            cashflows.append(row['amount'])
        dates.append(row['date'])
        
    # Append current value as a positive cashflow today
    cashflows.append(current_value)
    dates.append(pd.Timestamp.now())
    
    client_xirr = xirr(cashflows, dates)
    
    return {
        "aum": current_value,
        "net_investment": net_investment,
        "total_gain": total_gain,
        "xirr": client_xirr if client_xirr else 0.0
    }
