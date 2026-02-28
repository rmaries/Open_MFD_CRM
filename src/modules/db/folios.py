from .connection import BaseRepository

class FolioRepository(BaseRepository):
    """
    Manages Investment Folios. Folios are linked to CANs.
    """
    def add_folio(self, can_id, folio_number, amc_name):
        """Creates a new folio under a specific CAN ID."""
        query = 'INSERT INTO folios (can_id, folio_number, amc_name) VALUES (?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (int(can_id), folio_number, amc_name))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_folios_for_can(self, can_id):
        """Lists all folios registered under a particular CAN."""
        return self.run_query("SELECT * FROM folios WHERE can_id = ?", params=(int(can_id),))
