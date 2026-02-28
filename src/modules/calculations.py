import pandas as pd
import numpy as np
import numpy_financial as npf
from scipy.optimize import newton

def calculate_aum(df: pd.DataFrame) -> float:
    """
    Calculates the current Assets Under Management (AUM).
    Logic: Sum of (Units * Current NAV) for each transaction.
    A positive unit indicates a purchase, negative indicates a redemption.
    """
    if df.empty:
        return 0.0
    return (df['units'] * df['current_nav']).sum()

def xirr(cashflows, dates):
    """
    Calculate XIRR for a sequence of cashflows and dates.
    Standard financial math using Newton-Raphson optimization.
    """
    def xnpv(rate, cashflows, dates):
        d0 = dates[0]
        return sum([cf / (1 + rate)**((d - d0).days / 365.25) for cf, d in zip(cashflows, dates)])

    try:
        return newton(lambda r: xnpv(r, cashflows, dates), 0.1)
    except (RuntimeError, OverflowError):
        return None

def calculate_client_metrics(df: pd.DataFrame) -> dict:
    """
    Computes a comprehensive performance summary for a client's portfolio.
    Returns AUM, Net Investment, Total Gain/Loss, and XIRR.
    """
    metrics = {
        "aum": 0.0,
        "net_investment": 0.0,
        "total_gain": 0.0,
        "xirr": 0.0
    }
    
    if df.empty:
        return metrics

    # Ensure 'date' column is datetime for calculations
    df['date'] = pd.to_datetime(df['date'])

    # 1. Assets Under Management (Current Value)
    # This is the current market value of all holdings.
    metrics["aum"] = calculate_aum(df)
    
    # 2. Net Investment (Total Inflow - Total Outflow)
    # We use the 'amount' field which is the cost/proceeds of each transaction.
    # Purchases/SIP are positive inflows, Redemptions/SWP are negative outflows.
    metrics["net_investment"] = df['amount'].sum()
    
    # 3. Total Unrealized + Realized Gain
    # This is the difference between current AUM and the net amount invested.
    metrics["total_gain"] = metrics["aum"] - metrics["net_investment"]
    
    # 4. XIRR Calculation
    # XIRR requires a series of cashflows and corresponding dates.
    # Inflows (money going out of pocket, e.g., purchases) are negative.
    # Outflows (money coming into pocket, e.g., redemptions) are positive.
    cashflows = []
    dates = []
    
    for _, row in df.iterrows():
        if row['type'] in ['PURCHASE', 'SIP']:
            cashflows.append(-row['amount']) # Investment is a negative cashflow
        elif row['type'] in ['REDEMPTION', 'SWP']:
            cashflows.append(row['amount']) # Redemption is a positive cashflow
        dates.append(row['date'])
        
    # Terminal cashflow: Current AUM is treated as a positive cashflow today
    cashflows.append(metrics["aum"])
    dates.append(pd.Timestamp.now())
    
    client_xirr = xirr(cashflows, dates)
    metrics["xirr"] = client_xirr if client_xirr else 0.0
    return metrics
