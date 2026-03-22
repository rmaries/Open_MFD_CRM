import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from io import BytesIO

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from modules.db.database import Database

class TestNavIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_nav_integration.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('urllib.request.urlopen')
    def test_auto_fetch_on_add(self, mock_urlopen):
        # Mock AMFI data
        mock_data = (
            "Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date\r\n"
            "119063;INF209K01157;INF209K01165;HDFC Top 100 Fund - Growth;100.5500;04-Mar-2026\r\n"
        ).encode('utf-8')
        
        mock_response = MagicMock()
        mock_response.read.return_value = mock_data
        mock_urlopen.return_value = mock_response

        # Add scheme without NAV
        scheme_id = self.db.add_scheme("INF209K01157", "HDFC Top 100 Fund")
        
        schemes = self.db.get_all_schemes()
        self.assertEqual(len(schemes), 1)
        self.assertEqual(schemes.iloc[0]['current_nav'], 100.55)
        self.assertEqual(schemes.iloc[0]['last_updated'], "2026-03-04")

    @patch('urllib.request.urlopen')
    def test_bulk_update(self, mock_urlopen):
        # Initial data
        self.db.add_scheme("INF209K01157", "HDFC Top 100 Fund", current_nav=90.0)
        
        # Mock new AMFI data
        mock_data = (
            "Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date\r\n"
            "119063;INF209K01157;-;HDFC Top 100 Fund;105.2000;05-Mar-2026\r\n"
        ).encode('utf-8')
        
        mock_response = MagicMock()
        mock_response.read.return_value = mock_data
        mock_urlopen.return_value = mock_response

        # Update NAVs
        updated = self.db.update_scheme_navs()
        self.assertEqual(updated, 1)
        
        schemes = self.db.get_all_schemes()
        self.assertEqual(schemes.iloc[0]['current_nav'], 105.20)
        self.assertEqual(schemes.iloc[0]['last_updated'], "2026-03-05")

    def test_crud_operations(self):
        # Add
        scheme_id = self.db.add_scheme("TEST001", "Test Scheme", "Debt", 10.0)
        
        # Update
        success = self.db.update_scheme(scheme_id, scheme_name="Updated Test Name", category="Equity")
        self.assertTrue(success)
        
        schemes = self.db.get_all_schemes()
        updated_scheme = schemes[schemes['scheme_id'] == scheme_id].iloc[0]
        self.assertEqual(updated_scheme['scheme_name'], "Updated Test Name")
        self.assertEqual(updated_scheme['category'], "Equity")
        
        # Delete
        success = self.db.delete_scheme(scheme_id)
        self.assertTrue(success)
        
        schemes = self.db.get_all_schemes()
        self.assertEqual(len(schemes[schemes['scheme_id'] == scheme_id]), 0)

if __name__ == '__main__':
    unittest.main()

