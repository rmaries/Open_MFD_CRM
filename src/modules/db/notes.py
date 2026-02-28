from datetime import datetime
from .connection import BaseRepository

class NoteRepository(BaseRepository):
    """
    CRM module for tracking client interactions and notes.
    """
    def add_note(self, investor_id, content, category="General"):
        """Saves a timestamped meeting note or interaction record."""
        query = 'INSERT INTO notes (investor_id, content, category, created_at) VALUES (?, ?, ?, ?)'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (investor_id, content, category, now))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_notes(self, investor_id):
        """Fetches all notes for a specific client."""
        query = 'SELECT * FROM notes WHERE investor_id = ? ORDER BY created_at DESC'
        return self.run_query(query, params=(investor_id,))

    def search_notes(self, keyword):
        """Searches across all notes using SQL LIKE."""
        query = """
            SELECT n.*, c.name as client_name 
            FROM notes n 
            JOIN clients c ON n.investor_id = c.client_id 
            WHERE n.content LIKE ? OR n.category LIKE ?
        """
        return self.run_query(query, params=(f'%{keyword}%', f'%{keyword}%'))
