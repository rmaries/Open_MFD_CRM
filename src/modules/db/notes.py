from datetime import datetime
import pandas as pd
from .connection import BaseRepository
from .encryption import EncryptionMixin

class NoteRepository(EncryptionMixin, BaseRepository):
    """
    CRM module for tracking client interactions and notes.
    """
    def __init__(self, db_path: str, key: str = None):
        BaseRepository.__init__(self, db_path)
        EncryptionMixin.__init__(self, key)

    def add_note(self, client_id=None, can_id=None, content="", category="General"):
        """Saves a note linked to either a Client or a specific CAN."""
        # Ensure IDs are standard integers for SQLite compatibility (prevents numpy BLOB issues)
        cid = int(client_id) if client_id is not None else None
        canid = int(can_id) if can_id is not None else None
        
        query = 'INSERT INTO notes (client_id, can_id, content, category, created_at) VALUES (?, ?, ?, ?, ?)'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (cid, canid, content, category, now))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_notes(self, client_id=None, can_id=None):
        """Fetches notes for a specific client or CAN."""
        if can_id:
            query = 'SELECT * FROM notes WHERE can_id = ? ORDER BY created_at DESC'
            params = (int(can_id),)
        else:
            query = 'SELECT * FROM notes WHERE client_id = ? ORDER BY created_at DESC'
            params = (int(client_id) if client_id is not None else None,)
        return self.run_query(query, params=params)

    def search_notes(self, keyword):
        """Searches notes, specializing decrypted owner name in Python."""
        query = """
            SELECT n.*, cc.can_number, c.name as client_name 
            FROM notes n 
            LEFT JOIN clients c ON n.client_id = c.client_id 
            LEFT JOIN client_cans cc ON n.can_id = cc.id
            WHERE n.content LIKE ? OR n.category LIKE ?
        """
        df = self.run_query(query, params=(f'%{keyword}%', f'%{keyword}%'))
        if not df.empty:
            df['owner_name'] = df.apply(
                lambda row: self._decrypt(row['can_number']) if pd.notnull(row['can_number']) else row['client_name'], 
                axis=1
            )
        return df
