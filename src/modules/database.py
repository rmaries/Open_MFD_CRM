import sqlite3
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Database:
    def __init__(self, db_path=None):
        # Check for DB_PATH in environment variables first, then fallback to default
        if db_path is None:
            db_path = os.getenv("DB_PATH", "open_mfd.db")
        self.db_path = db_path
        self.init_db()

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
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (name, pan, can_number, email, phone, kyc_status, pan_card_url))
                return cursor.lastrowid
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
        finally:
            conn.close()

    def get_client_info(self, client_id):
        """Fetch full details for a single client."""
        query = "SELECT * FROM clients WHERE client_id = ?"
        df = self.run_query(query, params=(client_id,))
        return df.iloc[0].to_dict() if not df.empty else None

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
        return self.run_query("SELECT * FROM clients")
        
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
