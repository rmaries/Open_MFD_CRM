import pandas as pd
from .connection import BaseRepository

class ClientRepository(BaseRepository):
    """
    CRUD operations for clients and their associated CAN numbers.
    Stores all data in plain text.
    """
    def __init__(self, db_path: str, **kwargs):
        """
        Initialize the repository with a database path.
        """
        BaseRepository.__init__(self, db_path)
    
    def add_client(self, name, pan, can_number=None, email=None, phone=None, kyc_status=0, pan_card_url=None):
        """Creates a new client record and initial CAN entry."""
        query = '''
            INSERT INTO clients (name, pan, can_number, email, phone, kyc_status, pan_card_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (name, pan, can_number, email, phone, kyc_status, pan_card_url))
                client_id = cursor.lastrowid
                
            # If a CAN was provided on onboarding, register it in the multiple CANs table
            if can_number:
                self.add_client_can(client_id, can_number)
            
            return client_id
        finally:
            conn.close()

    def get_all_clients(self) -> pd.DataFrame:
        """Fetches all clients in plain text."""
        return self.run_query("SELECT * FROM clients")

    def get_client_info(self, client_id):
        """Fetches a single client's full profile including all registered CANs."""
        query = "SELECT * FROM clients WHERE client_id = ?"
        df = self.run_query(query, params=(client_id,))
        if not df.empty:
            info = df.iloc[0].to_dict()
            
            # Fetch the full list of CANs from the linked table
            cans_df = self.get_client_cans(client_id)
            info['all_cans'] = cans_df['can_number'].tolist() if not cans_df.empty else []
            return info
        return None

    def update_client_info(self, client_id, name=None, email=None, phone=None, can_number=None, pan=None):
        """Updates specific fields of a client profile."""
        updates = []
        params = []
        if name:
            updates.append("name = ?")
            params.append(name)
        if email:
            updates.append("email = ?")
            params.append(email)
        if phone:
            updates.append("phone = ?")
            params.append(phone)
        if can_number:
            updates.append("can_number = ?")
            params.append(can_number)
        if pan:
            updates.append("pan = ?")
            params.append(pan)
            
        if not updates:
            return

        query = f"UPDATE clients SET {', '.join(updates)} WHERE client_id = ?"
        params.append(client_id)
        
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(query, params)
            
            # Auto-link the new CAN if it's not already in the multiple CANs list
            if can_number:
                existing_cans = self.get_client_cans(client_id)
                can_list = existing_cans['can_number'].tolist() if not existing_cans.empty else []
                if can_number not in can_list:
                    self.add_client_can(client_id, can_number)
        finally:
            conn.close()

    def update_client_kyc(self, client_id, kyc_status):
        """Updates the KYC verification status (0 or 1)."""
        query = 'UPDATE clients SET kyc_status = ? WHERE client_id = ?'
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(query, (1 if kyc_status else 0, client_id))
        finally:
            conn.close()

    def add_client_can(self, client_id, can_number, can_description=None):
        """Registers an additional CAN number for a client."""
        if not can_number: return None
        query = 'INSERT INTO client_cans (client_id, can_number, can_description) VALUES (?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (client_id, can_number, can_description))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_client_cans(self, client_id) -> pd.DataFrame:
        """Retrieves all CANs associated with a client."""
        query = "SELECT * FROM client_cans WHERE client_id = ? ORDER BY created_at DESC"
        return self.run_query(query, params=(client_id,))

    def delete_client_can(self, can_id):
        """Removes a CAN record from the database if it has no associated folios."""
        # 1. Safety Check: Check for associated folios
        check_query = "SELECT count(*) FROM folios WHERE can_id = ?"
        df = self.run_query(check_query, params=(int(can_id),))
        folio_count = df.iloc[0, 0] if not df.empty else 0
        
        if folio_count > 0:
            return False, f"Cannot delete: CAN has {folio_count} associated folio(s)."

        # 2. Proceed with deletion
        query = "DELETE FROM client_cans WHERE id = ?"
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(query, (int(can_id),))
            return True, "CAN deleted successfully."
        finally:
            conn.close()
