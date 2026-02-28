from datetime import datetime
import pandas as pd
from .connection import BaseRepository
from .encryption import EncryptionMixin

class NoteRepository(BaseRepository):
    """
    CRM module for tracking client interactions and notes.
    """
    def __init__(self, db_path: str):
        BaseRepository.__init__(self, db_path)

    def add_note(self, client_id, content="", category="General"):
        """Saves a note linked to a Client."""
        # Ensure ID is standard integer for SQLite compatibility
        cid = int(client_id) if client_id is not None else None
        
        query = 'INSERT INTO notes (client_id, content, category, created_at) VALUES (?, ?, ?, ?)'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (cid, content, category, now))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_notes(self, client_id):
        """Fetches notes for a specific client."""
        query = 'SELECT * FROM notes WHERE client_id = ? ORDER BY created_at DESC'
        params = (int(client_id) if client_id is not None else None,)
        return self.run_query(query, params=params)

    def search_notes(self, keyword):
        """Searches notes, displaying client name."""
        query = """
            SELECT n.*, c.name as client_name 
            FROM notes n 
            LEFT JOIN clients c ON n.client_id = c.client_id 
            WHERE n.content LIKE ? OR n.category LIKE ?
        """
        df = self.run_query(query, params=(f'%{keyword}%', f'%{keyword}%'))
        if not df.empty:
            df['owner_name'] = df['client_name']
        return df
