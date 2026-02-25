from src.modules.database import Database
import os

def test_db():
    print("Testing Database Implementation...")
    # Ensure fresh start
    if os.path.exists("open_mfd.db"):
        os.remove("open_mfd.db")
        
    db = Database("open_mfd.db")
    
    # Add a client
    client_id = db.add_client("John Doe", "ABCDE1234F", "CAN123", "john@example.com", "9876543210")
    print(f"Added client with ID: {client_id}")
    
    # Add a folio
    folio_id = db.add_folio(client_id, "F123456", "HDFC Mutual Fund")
    print(f"Added folio with ID: {folio_id}")
    
    # Add a scheme (manually for now as we don't have API yet)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO schemes (isin_code, scheme_name, category, current_nav) VALUES (?, ?, ?, ?)", 
                       ("INF179K01844", "HDFC Index S&P BSE Sensex Fund", "Equity - Large Cap", 105.5))
        scheme_id = cursor.lastrowid
        conn.commit()
    print(f"Added scheme with ID: {scheme_id}")
    
    # Add a transaction
    trans_id = db.add_transaction(folio_id, scheme_id, "2024-02-24", "PURCHASE", 10000.0, 94.78, 105.5)
    print(f"Added transaction with ID: {trans_id}")
    
    # Verify portfolio
    portfolio = db.get_client_portfolio(client_id)
    print("\nClient Portfolio:")
    print(portfolio)
    
    if not portfolio.empty:
        print("\nTest PASSED!")
    else:
        print("\nTest FAILED!")

if __name__ == "__main__":
    test_db()
