import pandas as pd
import sqlite3
from .connection import BaseRepository

class TransactionRepository(BaseRepository):
    """
    Handles investment transactions and portfolio performance fetching.
    Stores all data in plain text.
    """
    def __init__(self, db_path: str, **kwargs):
        """Initialize with DB path."""
        BaseRepository.__init__(self, db_path)

    def add_transaction(self, folio_id, scheme_id, date, trans_type, amount, units, nav, order_number=None):
        """Records a new buy/sell/sip transaction. Returns rowid or None if duplicate order."""
        query = '''
            INSERT INTO transactions (folio_id, scheme_id, date, type, amount, units, nav_at_purchase, order_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (int(folio_id), int(scheme_id), date, trans_type, amount, units, nav, order_number))
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: transactions.order_number" in str(e):
                return None # Duplicate order
            raise e
        finally:
            conn.close()

    def get_client_portfolio(self, client_id, can_id=None) -> pd.DataFrame:
        """
        Retrieves a viewable ledger of all transactions for a client.
        Joins Transactions, Folios, CANs, and Schemes for a complete overview.
        Optionally filters by a specific can_id.
        """
        query = '''
            SELECT t.trans_id, cc.can_number, f.folio_number, f.amc_name, s.scheme_name, t.date, t.type, t.amount, t.units, t.nav_at_purchase
            FROM transactions t
            JOIN folios f ON t.folio_id = f.folio_id
            JOIN client_cans cc ON f.can_id = cc.id
            JOIN schemes s ON t.scheme_id = s.scheme_id
            WHERE cc.client_id = ?
        '''
        params = [client_id]
        if can_id:
            query += " AND cc.id = ?"
            params.append(can_id)
            
        return self.run_query(query, params=tuple(params))

    def get_total_metrics(self) -> dict:
        """Calculates global AUM (Assets Under Management) across all clients."""
        query = '''
            SELECT SUM(t.units * s.current_nav) as total_aum
            FROM transactions t
            JOIN schemes s ON t.scheme_id = s.scheme_id
        '''
        df = self.run_query(query)
        total = float(df['total_aum'].iloc[0]) if not df.empty and df['total_aum'].iloc[0] is not None else 0.0
        return {"total_aum": total}

    def get_transactions_for_calculations(self, client_id, can_id=None) -> pd.DataFrame:
        """
        Specialized fetch for financial math (calculations.py).
        Returns raw units and current NAV for AUM/XIRR computing without manual joins.
        Optionally filters by a specific can_id.
        """
        query = '''
            SELECT t.trans_id, t.date, t.amount, t.type, t.units, s.current_nav
            FROM transactions t
            JOIN folios f ON t.folio_id = f.folio_id
            JOIN client_cans cc ON f.can_id = cc.id
            JOIN schemes s ON t.scheme_id = s.scheme_id
            WHERE cc.client_id = ?
        '''
        params = [client_id]
        if can_id:
            query += " AND cc.id = ?"
            params.append(can_id)
            
        return self.run_query(query, params=tuple(params))

    def update_transaction(self, trans_id, folio_id, scheme_id, date, trans_type, amount, units, nav, order_number=None):
        """Updates an existing transaction."""
        query = '''
            UPDATE transactions
            SET folio_id = ?, scheme_id = ?, date = ?, type = ?, amount = ?, units = ?, nav_at_purchase = ?, order_number = ?
            WHERE trans_id = ?
        '''
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (int(folio_id), int(scheme_id), date, trans_type, amount, units, nav, order_number, int(trans_id)))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_transaction(self, trans_id):
        """Deletes a transaction by its ID."""
        query = '''
            DELETE FROM transactions WHERE trans_id = ?
        '''
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (int(trans_id),))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def get_transaction(self, trans_id) -> dict:
        """Fetches a single transaction's full details by ID."""
        query = '''
            SELECT trans_id, folio_id, scheme_id, date, type, amount, units, nav_at_purchase, order_number
            FROM transactions
            WHERE trans_id = ?
        '''
        df = self.run_query(query, params=(int(trans_id),))
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
