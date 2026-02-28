import pandas as pd
from .connection import BaseRepository
from .encryption import EncryptionMixin

class ClientRepository(EncryptionMixin, BaseRepository):
    """
    CRUD operations for clients and their associated CAN numbers.
    Extends EncryptionMixin to handle PII (Personally Identifiable Information).
    """
    def __init__(self, db_path: str, key: str = None):
        """
        Initialize the repository with a database path and optional encryption key.
        Explicitly calls constructors for both parents in the diamond inheritance.
        """
        BaseRepository.__init__(self, db_path)
        EncryptionMixin.__init__(self, key)
    
    def add_client(self, name, pan, can_number=None, email=None, phone=None, kyc_status=0, pan_card_url=None):
        """Creates a new client record and initial CAN entry."""
        query = '''
            INSERT INTO clients (name, pan, can_number, email, phone, kyc_status, pan_card_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        # Encrypt sensitive fields before database insertion
        enc_pan = self._encrypt(pan)
        enc_email = self._encrypt(email)
        enc_phone = self._encrypt(phone)
        enc_can = self._encrypt(can_number)
        
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (name, enc_pan, enc_can, enc_email, enc_phone, kyc_status, pan_card_url))
                client_id = cursor.lastrowid
                
            # If a CAN was provided on onboarding, register it in the multiple CANs table
            if can_number:
                self.add_client_can(client_id, can_number)
            
            return client_id
        finally:
            conn.close()

    def get_all_clients(self) -> pd.DataFrame:
        """Fetches all clients and decrypts sensitive fields for display."""
        df = self.run_query("SELECT * FROM clients")
        if not df.empty:
            df['pan'] = df['pan'].apply(self._decrypt)
            df['email'] = df['email'].apply(self._decrypt)
            df['phone'] = df['phone'].apply(self._decrypt)
            df['can_number'] = df['can_number'].apply(self._decrypt)
        return df

    def get_client_info(self, client_id):
        """Fetches a single client's full profile including all registered CANs."""
        query = "SELECT * FROM clients WHERE client_id = ?"
        df = self.run_query(query, params=(client_id,))
        if not df.empty:
            info = df.iloc[0].to_dict()
            info['pan'] = self._decrypt(info['pan'])
            info['email'] = self._decrypt(info['email'])
            info['phone'] = self._decrypt(info['phone'])
            info['can_number'] = self._decrypt(info['can_number'])
            
            # Fetch the full list of CANs from the linked table
            cans_df = self.get_client_cans(client_id)
            info['all_cans'] = cans_df['can_number'].tolist() if not cans_df.empty else []
            return info
        return None

    def update_client_info(self, client_id, name=None, email=None, phone=None, can_number=None, pan=None):
        """Updates specific fields of a client profile with new encrypted values."""
        updates = []
        params = []
        if name:
            updates.append("name = ?")
            params.append(name)
        if email:
            updates.append("email = ?")
            params.append(self._encrypt(email))
        if phone:
            updates.append("phone = ?")
            params.append(self._encrypt(phone))
        if can_number:
            updates.append("can_number = ?")
            params.append(self._encrypt(can_number))
        if pan:
            updates.append("pan = ?")
            params.append(self._encrypt(pan))
            
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
        enc_can = self._encrypt(can_number)
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (client_id, enc_can, can_description))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_client_cans(self, client_id) -> pd.DataFrame:
        """Retrieves and decrypts all CANs associated with a client."""
        query = "SELECT * FROM client_cans WHERE client_id = ? ORDER BY created_at DESC"
        df = self.run_query(query, params=(client_id,))
        if not df.empty:
            df['can_number'] = df['can_number'].apply(self._decrypt)
        return df

    def delete_client_can(self, can_id):
        """Removes a CAN record from the database."""
        query = "DELETE FROM client_cans WHERE id = ?"
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(query, (int(can_id),))
            return True
        finally:
            conn.close()
