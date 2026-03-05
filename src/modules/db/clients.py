import pandas as pd
import sqlite3
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
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: clients.pan" in str(e):
                raise Exception(f"PAN '{pan}' is already registered for another client.")
            raise e
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
                success, message = self.add_client_can(selected_client_id=client_id, can_number=can_number)
                # We don't necessarily want to block profile update if CAN link fails because it's already linked
                # but we should be aware of it.
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: clients.pan" in str(e):
                raise Exception(f"PAN '{pan}' is already registered for another client.")
            raise e
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

    def add_client_can(self, client_id=None, can_number=None, can_description=None, selected_client_id=None):
        """Registers an additional CAN number for a client."""
        # Handle cases where client_id might be passed as second arg or keyword
        cid = client_id or selected_client_id
        if not can_number or not cid: 
            return False, "Missing CAN number or client ID"
            
        # Check if CAN already exists
        check_query = "SELECT client_id FROM client_cans WHERE can_number = ?"
        existing = self.run_query(check_query, params=(can_number,))
        if not existing.empty:
            owner_id = existing.iloc[0, 0]
            if owner_id == cid:
                return True, "CAN already linked to this client."
            else:
                return False, f"CAN '{can_number}' is already registered to another client."

        query = 'INSERT INTO client_cans (client_id, can_number, can_description) VALUES (?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (cid, can_number, can_description))
                return True, f"CAN '{can_number}' added successfully."
        except sqlite3.IntegrityError:
             return False, f"CAN '{can_number}' is already registered."
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

    def delete_client(self, client_id):
        """
        Permanently deletes a client and ALL associated data (CANs, Folios, Transactions, etc.).
        Also removes physical documents.
        """
        conn = self.get_connection()
        try:
            with conn:
                # 1. Get all associated CAN IDs
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM client_cans WHERE client_id = ?", (client_id,))
                can_ids = [row[0] for row in cursor.fetchall()]
                
                # 2. Get all associated Folio IDs
                folio_ids = []
                if can_ids:
                    placeholders = ', '.join(['?'] * len(can_ids))
                    cursor.execute(f"SELECT folio_id FROM folios WHERE can_id IN ({placeholders})", can_ids)
                    folio_ids = [row[0] for row in cursor.fetchall()]

                # 3. Cascaded Deletion (Order matters for FKs)
                # Transactions
                if folio_ids:
                    placeholders = ', '.join(['?'] * len(folio_ids))
                    cursor.execute(f"DELETE FROM transactions WHERE folio_id IN ({placeholders})", folio_ids)
                
                # Folios
                if can_ids:
                    placeholders = ', '.join(['?'] * len(can_ids))
                    cursor.execute(f"DELETE FROM folios WHERE can_id IN ({placeholders})", can_ids)
                
                # CANs, Notes, Tasks, Documents (linked directly to client_id)
                cursor.execute("DELETE FROM client_cans WHERE client_id = ?", (client_id,))
                cursor.execute("DELETE FROM notes WHERE client_id = ?", (client_id,))
                cursor.execute("DELETE FROM tasks WHERE client_id = ?", (client_id,))
                cursor.execute("DELETE FROM documents WHERE client_id = ?", (client_id,))
                cursor.execute("DELETE FROM clients WHERE client_id = ?", (client_id,))
            
            # 4. Cleanup physical documents
            import shutil
            import os
            base_dir = "data/documents"
            client_dir = os.path.join(base_dir, f"client_{client_id}")
            if os.path.exists(client_dir):
                shutil.rmtree(client_dir)
                
            return True, "Client and all associated data deleted successfully."
        except Exception as e:
            return False, f"Error deleting client: {str(e)}"
        finally:
            conn.close()
