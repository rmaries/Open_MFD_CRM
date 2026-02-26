import sys
import os
import time
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from modules.database import Database

def test_scalability():
    db_file = "test_scalability.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    
    db = Database(db_file)
    
    print("Seeding database with 100 clients and transactions...")
    start_seed = time.time()
    for i in range(100):
        client_id = db.add_client(f"Client {i}", f"PAN{i:05}", f"CAN{i:05}")
        folio_id = db.add_folio(client_id, f"FOL{i:05}", "Test AMC")
        # Add a scheme if not exists
        conn = db.get_connection()
        try:
            with conn:
                conn.execute("INSERT OR IGNORE INTO schemes (isin_code, scheme_name, current_nav) VALUES (?, ?, ?)", 
                             (f"ISIN{i}", f"Scheme {i}", 100.0))
                scheme_id = conn.execute("SELECT scheme_id FROM schemes WHERE isin_code = ?", (f"ISIN{i}",)).fetchone()[0]
        finally:
            conn.close()
        
        db.add_transaction(folio_id, scheme_id, "2023-01-01", "PURCHASE", 10000.0, 100.0, 100.0)
    
    print(f"Seeding took {time.time() - start_seed:.2f} seconds.")
    
    print("\nMeasuring performance of get_total_metrics()...")
    start_op = time.time()
    metrics = db.get_total_metrics()
    end_op = time.time()
    
    print(f"Total AUM: {metrics['total_aum']}")
    print(f"Time taken: {(end_op - start_op)*1000:.2f} ms")
    
    # Verify correctness
    expected_aum = 100 * 100.0 * 100.0 # 100 clients * 100 units * 100 NAV
    if metrics['total_aum'] == expected_aum:
        print("\nSUCCESS: Calculation is correct!")
    else:
        print(f"\nFAILURE: Calculation mismatch. Expected {expected_aum}, got {metrics['total_aum']}")

    # Final verification and instructions
    print(f"\n" + "="*50)
    print("PORTABLE TEST DATABASE READY")
    print("="*50)
    print(f"File created: {os.path.abspath(db_file)}")
    print("\nTo see the app with this data:")
    print("1. Close any running instances of the app.")
    print(f"2. Ensure your .env file has: DB_PATH={db_file}")
    print("3. Run: python run_app.py")
    print("\nTo delete the test database later:")
    print(f"Run: del {db_file}")
    print("="*50)

    # Note: Cleanup logic removed so you can inspect the file.

if __name__ == "__main__":
    test_scalability()
