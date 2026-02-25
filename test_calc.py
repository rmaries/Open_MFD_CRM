from src.modules.database import Database
from src.modules.calculations import calculate_client_metrics
import os
import pandas as pd

def test_calculations():
    print("Testing Financial Calculations...")
    db_path = "test_calc.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db = Database(db_path)
    
    # 1. Setup Data
    client_id = db.add_client("Test Investor", "PAN12345", "CAN789")
    folio_id = db.add_folio(client_id, "F999", "Test AMC")
    
    # Add Scheme
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO schemes (isin_code, scheme_name, category, current_nav) VALUES (?, ?, ?, ?)", 
                       ("TEST_ISIN", "Nifty 50 Index Fund", "Equity", 150.0))
        scheme_id = cursor.lastrowid
        conn.commit()

    # 2. Add Transactions
    # Buy 1 year ago: 10,000 at NAV 100 (100 units)
    date_1yr_ago = (pd.Timestamp.now() - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    db.add_transaction(folio_id, scheme_id, date_1yr_ago, "PURCHASE", 10000.0, 100.0, 100.0)
    
    # Buy 6 months ago: 5,000 at NAV 125 (40 units)
    date_6mo_ago = (pd.Timestamp.now() - pd.DateOffset(months=6)).strftime('%Y-%m-%d')
    db.add_transaction(folio_id, scheme_id, date_6mo_ago, "PURCHASE", 5000.0, 40.0, 125.0)
    
    # Total units: 140. Current NAV: 150. Current Value: 140 * 150 = 21,000
    # Net Invested: 10,000 + 5,000 = 15,000
    # Total Gain: 21,000 - 15,000 = 6,000
    
    # 3. Verify Metrics
    metrics = calculate_client_metrics(client_id, db)
    print("\nCalculated Metrics:")
    for key, value in metrics.items():
        if key == "xirr":
            print(f"{key}: {value:.2%}")
        else:
            print(f"{key}: {value:,.2f}")
            
    # Simple Assertions
    assert metrics['aum'] == 21000.0
    assert metrics['net_investment'] == 15000.0
    assert metrics['total_gain'] == 6000.0
    assert metrics['xirr'] > 0  # Should be positive
    
    print("\nTest PASSED!")

if __name__ == "__main__":
    test_calculations()
