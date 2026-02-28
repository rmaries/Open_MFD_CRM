import pandas as pd
from .connection import BaseRepository
from .encryption import EncryptionMixin

class TransactionRepository(EncryptionMixin, BaseRepository):
    """
    Handles investment transactions and portfolio performance fetching.
    """
    def __init__(self, db_path: str, key: str = None):
        """Initialize with DB path and encryption support."""
        BaseRepository.__init__(self, db_path)
        EncryptionMixin.__init__(self, key)

    def add_transaction(self, folio_id, scheme_id, date, trans_type, amount, units, nav):
        """Records a new buy/sell/sip transaction."""
        query = '''
            INSERT INTO transactions (folio_id, scheme_id, date, type, amount, units, nav_at_purchase)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (folio_id, scheme_id, date, trans_type, amount, units, nav))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_client_portfolio(self, client_id, can_id=None) -> pd.DataFrame:
        """
        Retrieves a viewable ledger of all transactions for a client.
        Joins Transactions, Folios, CANs, and Schemes for a complete overview.
        Optionally filters by a specific can_id.
        """
        query = '''
            SELECT cc.can_number, f.folio_number, f.amc_name, s.scheme_name, t.date, t.type, t.amount, t.units, t.nav_at_purchase
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
            
        df = self.run_query(query, params=tuple(params))
        if not df.empty:
            df['can_number'] = df['can_number'].apply(self._decrypt)
        return df

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
            SELECT t.date, t.amount, t.type, t.units, s.current_nav
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
