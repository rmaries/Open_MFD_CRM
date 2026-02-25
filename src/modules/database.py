import sqlite3
import pandas as pd
from datetime import datetime

class Database:
    def __init__(self, db_path="open_mfd.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table A: clients
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    pan TEXT UNIQUE NOT NULL,
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

    def run_query(self, query, params=None):
        with self.get_connection() as conn:
            return pd.read_sql(query, conn, params=params)

    def add_client(self, name, pan, can_number=None, email=None, phone=None, kyc_status=0, pan_card_url=None):
        query = '''
            INSERT INTO clients (name, pan, can_number, email, phone, kyc_status, pan_card_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name, pan, can_number, email, phone, kyc_status, pan_card_url))
            conn.commit()
            return cursor.lastrowid

    def add_folio(self, client_id, folio_number, amc_name):
        query = 'INSERT INTO folios (client_id, folio_number, amc_name) VALUES (?, ?, ?)'
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (client_id, folio_number, amc_name))
            conn.commit()
            return cursor.lastrowid

    def add_transaction(self, folio_id, scheme_id, date, trans_type, amount, units, nav):
        query = '''
            INSERT INTO transactions (folio_id, scheme_id, date, type, amount, units, nav_at_purchase)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (folio_id, scheme_id, date, trans_type, amount, units, nav))
            conn.commit()
            return cursor.lastrowid
            
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

    # Note Methods
    def add_note(self, investor_id, content, category="General"):
        query = 'INSERT INTO notes (investor_id, content, category, created_at) VALUES (?, ?, ?, ?)'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (investor_id, content, category, now))
            conn.commit()
            return cursor.lastrowid

    def get_notes(self, investor_id):
        query = 'SELECT * FROM notes WHERE investor_id = ? ORDER BY created_at DESC'
        return self.run_query(query, params=(investor_id,))

    def search_notes(self, keyword):
        query = "SELECT n.*, c.name as client_name FROM notes n JOIN clients c ON n.investor_id = c.client_id WHERE n.content LIKE ? OR n.category LIKE ?"
        return self.run_query(query, params=(f'%{keyword}%', f'%{keyword}%'))

    # Task Methods
    def add_task(self, investor_id, description, due_date, status="Pending", priority="Med"):
        query = 'INSERT INTO tasks (investor_id, description, due_date, status, priority) VALUES (?, ?, ?, ?, ?)'
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (investor_id, description, due_date, status, priority))
            conn.commit()
            return cursor.lastrowid

    def update_task_status(self, task_id, status):
        query = 'UPDATE tasks SET status = ? WHERE id = ?'
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (status, task_id))
            conn.commit()

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
