import sqlite3
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import shutil

# Load environment variables from .env file
load_dotenv()

class Database:
    def __init__(self, db_path=None):
        # Check for DB_PATH in environment variables first, then fallback to default
        if db_path is None:
            db_path = os.getenv("DB_PATH", "open_mfd.db")
        self.db_path = db_path
        
        # Encryption Setup
        self.key = os.getenv("FERNET_KEY")
        if not self.key:
            # For portable mode, we generate a key if missing
            self.key = Fernet.generate_key().decode()
            print("WARNING: No FERNET_KEY found. Generated a new one.")
        
        # Ensure key is clean of whitespace
        clean_key = self.key.strip().encode()
        self.cipher = Fernet(clean_key)
        
        self.init_db()

    def _encrypt(self, text):
        if not text: return None
        return self.cipher.encrypt(str(text).encode()).decode()

    def _decrypt(self, encrypted_text):
        if not encrypted_text: return None
        try:
            return self.cipher.decrypt(str(encrypted_text).encode()).decode()
        except:
            return encrypted_text # Fallback for legacy plain data

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Table A: clients
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    pan TEXT UNIQUE,
                    can_number TEXT,
                    email TEXT,
                    phone TEXT,
                    kyc_status BOOLEAN DEFAULT 0,
                    pan_card_url TEXT,
                    onboarding_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table B: folios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folios (
                    folio_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    folio_number TEXT NOT NULL,
                    amc_name TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (client_id) REFERENCES clients (client_id)
                )
            ''')
            
            # Table C: schemes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schemes (
                    scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isin_code TEXT UNIQUE,
                    scheme_name TEXT NOT NULL,
                    category TEXT,
                    current_nav REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table D: transactions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    trans_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folio_id INTEGER,
                    scheme_id INTEGER,
                    date DATE NOT NULL,
                    type TEXT CHECK(type IN ('PURCHASE', 'REDEMPTION', 'SIP', 'STP', 'SWP')),
                    amount REAL,
                    units REAL,
                    nav_at_purchase REAL,
                    FOREIGN KEY (folio_id) REFERENCES folios (folio_id),
                    FOREIGN KEY (scheme_id) REFERENCES schemes (scheme_id)
                )
            ''')

            # Table E: notes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investor_id INTEGER,
                    content TEXT NOT NULL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (investor_id) REFERENCES clients (client_id)
                )
            ''')

            # Table F: tasks
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investor_id INTEGER,
                    description TEXT NOT NULL,
                    due_date DATE,
                    status TEXT CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')) DEFAULT 'Pending',
                    priority TEXT CHECK(priority IN ('High', 'Med', 'Low')) DEFAULT 'Med',
                    FOREIGN KEY (investor_id) REFERENCES clients (client_id)
                )
            ''')

            # Table G: documents
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    doc_type TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients (client_id)
                )
            ''')
            # Table H: client_cans
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS client_cans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    can_number TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients (client_id)
                )
            ''')
            
            # Migration: Move existing CANs from clients table to client_cans
            # We check if we already moved them by checking if client_cans is empty 
            # while clients has data with can_number
            cursor.execute("SELECT count(*) FROM client_cans")
            if cursor.fetchone()[0] == 0:
                cursor.execute("SELECT client_id, can_number FROM clients WHERE can_number IS NOT NULL AND can_number != ''")
                existing_cans = cursor.fetchall()
                for client_id, can in existing_cans:
                    cursor.execute("INSERT INTO client_cans (client_id, can_number) VALUES (?, ?)", (client_id, can))

            conn.commit()
        finally:
            conn.close()

    def run_query(self, query, params=None):
        conn = self.get_connection()
        try:
            return pd.read_sql(query, conn, params=params)
        finally:
            conn.close()

    def add_client(self, name, pan, can_number=None, email=None, phone=None, kyc_status=0, pan_card_url=None):
        query = '''
            INSERT INTO clients (name, pan, can_number, email, phone, kyc_status, pan_card_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        # Encrypt sensitive fields
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
                
            # Add to multiple CANs table as well
            if can_number:
                self.add_client_can(client_id, can_number)
            
            return client_id
        finally:
            conn.close()

    def update_client_kyc(self, client_id, kyc_status):
        query = 'UPDATE clients SET kyc_status = ? WHERE client_id = ?'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (1 if kyc_status else 0, client_id))
        finally:
            conn.close()

    def update_client_info(self, client_id, name=None, email=None, phone=None, can_number=None, pan=None):
        """Update client personal information."""
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
                
            # If CAN was updated, add it to the multiple CANs list as well
            if can_number:
                # Check if it already exists in the list to avoid duplicates
                existing_cans = self.get_client_cans(client_id)
                can_list = existing_cans['can_number'].tolist() if not existing_cans.empty else []
                if can_number not in can_list:
                    self.add_client_can(client_id, can_number)
        finally:
            conn.close()

    def get_client_info(self, client_id):
        """Fetch full details for a single client."""
        query = "SELECT * FROM clients WHERE client_id = ?"
        df = self.run_query(query, params=(client_id,))
        if not df.empty:
            info = df.iloc[0].to_dict()
            info['pan'] = self._decrypt(info['pan'])
            info['email'] = self._decrypt(info['email'])
            info['phone'] = self._decrypt(info['phone'])
            info['can_number'] = self._decrypt(info['can_number'])
            
            # Fetch all associated CANs
            cans_df = self.get_client_cans(client_id)
            info['all_cans'] = cans_df['can_number'].tolist() if not cans_df.empty else []
            return info
        return None

    def add_client_can(self, client_id, can_number):
        """Add a new CAN number to a client."""
        if not can_number: return None
        query = 'INSERT INTO client_cans (client_id, can_number) VALUES (?, ?)'
        enc_can = self._encrypt(can_number)
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (client_id, enc_can))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_client_cans(self, client_id):
        """Retrieve all CAN numbers for a specific client."""
        query = "SELECT * FROM client_cans WHERE client_id = ? ORDER BY created_at DESC"
        df = self.run_query(query, params=(client_id,))
        if not df.empty:
            df['can_number'] = df['can_number'].apply(self._decrypt)
        return df

    def delete_client_can(self, can_id):
        """Delete a specific CAN number."""
        query = "DELETE FROM client_cans WHERE id = ?"
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (int(can_id),))
            return True
        finally:
            conn.close()

    def add_document(self, client_id, file_obj, doc_type="Other"):
        """Save an encrypted file and track it in the DB."""
        base_dir = "data/documents"
        client_dir = os.path.join(base_dir, f"client_{client_id}")
        os.makedirs(client_dir, exist_ok=True)
        
        file_path = os.path.join(client_dir, file_obj.name)
        
        # Encrypt file content before saving
        plain_content = bytes(file_obj.getbuffer())
        encrypted_content = self.cipher.encrypt(plain_content)
        
        with open(file_path, "wb") as f:
            f.write(encrypted_content)
        
        # Track in DB
        query = 'INSERT INTO documents (client_id, file_name, file_path, doc_type) VALUES (?, ?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (client_id, file_obj.name, file_path, doc_type))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_document_content(self, doc_id):
        """Read and decrypt file content from disk."""
        query = "SELECT file_path FROM documents WHERE doc_id = ?"
        df = self.run_query(query, params=(doc_id,))
        if df.empty:
            return None
        
        file_path = df.iloc[0]['file_path']
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, "rb") as f:
                encrypted_content = f.read()
            
            # Decrypt
            return self.cipher.decrypt(encrypted_content)
        except Exception as e:
            print(f"Decryption error: {e}")
            # Fallback for plain-text legacy files if any
            with open(file_path, "rb") as f:
                return f.read()

    def get_documents(self, client_id):
        """Retrieve documents for a specific client."""
        query = "SELECT * FROM documents WHERE client_id = ? ORDER BY uploaded_at DESC"
        return self.run_query(query, params=(client_id,))

    def delete_document(self, doc_id):
        """Delete a document from both disk and DB."""
        # 1. Get path
        query = "SELECT file_path FROM documents WHERE doc_id = ?"
        df = self.run_query(query, params=(doc_id,))
        if df.empty:
            return False
        
        file_path = df.iloc[0]['file_path']
        
        # 2. Delete file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
            # Continue to delete DB record even if file delete fails
            
        # 3. Delete from DB
        delete_query = "DELETE FROM documents WHERE doc_id = ?"
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(delete_query, (doc_id,))
                return True
        finally:
            conn.close()

    def add_folio(self, client_id, folio_number, amc_name):
        query = 'INSERT INTO folios (client_id, folio_number, amc_name) VALUES (?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (client_id, folio_number, amc_name))
                return cursor.lastrowid
        finally:
            conn.close()

    def add_transaction(self, folio_id, scheme_id, date, trans_type, amount, units, nav):
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
            
    def get_all_clients(self):
        df = self.run_query("SELECT * FROM clients")
        # Decrypt sensitive fields
        if not df.empty:
            df['pan'] = df['pan'].apply(self._decrypt)
            df['email'] = df['email'].apply(self._decrypt)
            df['phone'] = df['phone'].apply(self._decrypt)
            df['can_number'] = df['can_number'].apply(self._decrypt)
        return df
        
    def get_client_portfolio(self, client_id):
        query = '''
            SELECT f.folio_number, f.amc_name, s.scheme_name, t.date, t.type, t.amount, t.units, t.nav_at_purchase
            FROM transactions t
            JOIN folios f ON t.folio_id = f.folio_id
            JOIN schemes s ON t.scheme_id = s.scheme_id
            WHERE f.client_id = ?
        '''
        return self.run_query(query, params=(client_id,))

    def get_total_metrics(self):
        """Calculate aggregate metrics across all clients efficiently."""
        query = '''
            SELECT SUM(t.units * s.current_nav) as total_aum
            FROM transactions t
            JOIN schemes s ON t.scheme_id = s.scheme_id
        '''
        df = self.run_query(query)
        return {
            "total_aum": float(df['total_aum'].iloc[0]) if not df.empty and df['total_aum'].iloc[0] is not None else 0.0
        }

    # Note Methods
    def add_note(self, investor_id, content, category="General"):
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
        query = 'SELECT * FROM notes WHERE investor_id = ? ORDER BY created_at DESC'
        return self.run_query(query, params=(investor_id,))

    def search_notes(self, keyword):
        query = "SELECT n.*, c.name as client_name FROM notes n JOIN clients c ON n.investor_id = c.client_id WHERE n.content LIKE ? OR n.category LIKE ?"
        return self.run_query(query, params=(f'%{keyword}%', f'%{keyword}%'))

    # Task Methods
    def add_task(self, investor_id, description, due_date, status="Pending", priority="Med"):
        query = 'INSERT INTO tasks (investor_id, description, due_date, status, priority) VALUES (?, ?, ?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (investor_id, description, due_date, status, priority))
                return cursor.lastrowid
        finally:
            conn.close()

    def update_task_status(self, task_id, status):
        query = 'UPDATE tasks SET status = ? WHERE id = ?'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (status, task_id))
        finally:
            conn.close()

    def get_tasks(self, investor_id=None):
        if investor_id:
            query = 'SELECT * FROM tasks WHERE investor_id = ? ORDER BY due_date ASC'
            return self.run_query(query, params=(investor_id,))
        else:
            query = "SELECT t.*, c.name as client_name FROM tasks t JOIN clients c ON t.investor_id = c.client_id ORDER BY due_date ASC"
            return self.run_query(query)

    def get_overdue_tasks(self):
        query = """
            SELECT t.*, c.name as client_name 
            FROM tasks t 
            JOIN clients c ON t.investor_id = c.client_id 
            WHERE t.due_date < DATE('now') AND t.status NOT IN ('Completed', 'Cancelled')
        """
        return self.run_query(query)
