import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from modules.db.database import Database

def test_schemes():
    db_path = "test_schemes.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = Database(db_path)
    
    print("Testing manual scheme addition...")
    scheme_id = db.add_scheme("INF209K01157", "HDFC Top 100 Fund", "Equity", 100.55)
    print(f"Added scheme ID: {scheme_id}")
    
    schemes = db.get_all_schemes()
    print(f"Total schemes: {len(schemes)}")
    assert len(schemes) == 1
    assert schemes.iloc[0]['scheme_code'] == "INF209K01157"
    
    print("Testing bulk import...")
    import_data = pd.DataFrame([
        {'scheme_code': 'INF209K01157', 'scheme_name': 'HDFC Top 100 Fund (Updated)', 'category': 'Equity', 'current_nav': 101.00},
        {'scheme_code': 'INF179K01RY1', 'scheme_name': 'HDFC Mid-Cap Opportunities Fund', 'category': 'Equity', 'current_nav': 120.45}
    ])
    
    count = db.bulk_import_schemes(import_data)
    print(f"Imported/Updated {count} schemes")
    
    schemes = db.get_all_schemes()
    print(f"Total schemes after bulk import: {len(schemes)}")
    assert len(schemes) == 2
    
    # Verify update (upsert)
    hdfc_top_100 = schemes[schemes['scheme_code'] == "INF209K01157"].iloc[0]
    assert hdfc_top_100['scheme_name'] == "HDFC Top 100 Fund (Updated)"
    assert hdfc_top_100['current_nav'] == 101.00
    
    print("All backend scheme tests passed!")
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_schemes()
