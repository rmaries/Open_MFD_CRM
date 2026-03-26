from .connection import BaseRepository

class SchemaManager(BaseRepository):
    """
    Responsible for DDL (Data Definition Language) operations.
    Handles table creation and structural migrations to keep the DB schema in sync with code requirements.
    """
    def init_db(self):
        """
        Initializes the entire database schema.
        Orchestrates table creation and migration runs.
        Idempotent: Only creates tables if they don't already exist.
        """
        self._create_tables()
        self._run_migrations()

    def _create_tables(self):
        """
        Creates all necessary tables in the database if they don't already exist.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Clients table
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
            
            # Folios table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folios (
                    folio_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    can_id INTEGER,
                    folio_number TEXT NOT NULL,
                    amc_name TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (can_id) REFERENCES client_cans (id)
                )
            ''')
            
            # Schemes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schemes (
                    scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scheme_code TEXT UNIQUE,
                    rta_code TEXT,
                    scheme_name TEXT NOT NULL,
                    category TEXT,
                    current_nav REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Transactions table
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
                    order_number TEXT UNIQUE,
                    FOREIGN KEY (folio_id) REFERENCES folios (folio_id),
                    FOREIGN KEY (scheme_id) REFERENCES schemes (scheme_id)
                )
            ''')

            # Notes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    content TEXT NOT NULL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients (client_id)
                )
            ''')

            # Tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    description TEXT NOT NULL,
                    due_date DATE,
                    status TEXT CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')) DEFAULT 'Pending',
                    priority TEXT CHECK(priority IN ('High', 'Med', 'Low')) DEFAULT 'Med',
                    FOREIGN KEY (client_id) REFERENCES clients (client_id)
                )
            ''')

            # Documents table
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

            # Client CANs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS client_cans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    can_number TEXT NOT NULL UNIQUE,
                    can_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients (client_id)
                )
            ''')
            
            conn.commit()
        finally:
            conn.close()

    def _run_migrations(self):
        """
        Executes one-time schema migrations.
        These migrations are designed to be idempotent.
        """
        self._migrate_cans_to_table()
        self._migrate_folios_to_cans()
        self._revert_notes_tasks_linkage()
        self._add_can_description_to_client_cans()
        self._enforce_can_uniqueness()
        self._rename_isin_code_to_scheme_code()
        self._add_rta_code_to_schemes()
        self._add_order_number_to_transactions()

    def _add_can_description_to_client_cans(self):
        """Adds can_description column to client_cans table if it doesn't exist."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(client_cans)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'can_description' not in columns:
                cursor.execute("ALTER TABLE client_cans ADD COLUMN can_description TEXT")
            conn.commit()
        finally:
            conn.close()

    def _migrate_cans_to_table(self):
        """
        Migration: Moves legacy CAN numbers from the 'clients' table into the new 'client_cans' table.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM client_cans")
            if cursor.fetchone()[0] == 0:
                cursor.execute("SELECT client_id, can_number FROM clients WHERE can_number IS NOT NULL AND can_number != ''")
                existing_cans = cursor.fetchall()
                for client_id, can in existing_cans:
                    cursor.execute("INSERT INTO client_cans (client_id, can_number) VALUES (?, ?)", (client_id, can))
                conn.commit()
        finally:
            conn.close()

    def _migrate_folios_to_cans(self):
        """Adjusts folios table to link to CANs instead of directly to Clients."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(folios)")
            folio_cols = [row[1] for row in cursor.fetchall()]
            
            if 'client_id' in folio_cols and 'can_id' not in folio_cols:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS folios_new (
                        folio_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        can_id INTEGER,
                        folio_number TEXT NOT NULL,
                        amc_name TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (can_id) REFERENCES client_cans (id)
                    )
                ''')
                cursor.execute('''
                    INSERT INTO folios_new (folio_id, can_id, folio_number, amc_name, is_active)
                    SELECT f.folio_id,
                           (SELECT cc.id FROM client_cans cc WHERE cc.client_id = f.client_id ORDER BY cc.id LIMIT 1),
                           f.folio_number, f.amc_name, f.is_active
                    FROM folios f
                    WHERE (SELECT cc.id FROM client_cans cc WHERE cc.client_id = f.client_id ORDER BY cc.id LIMIT 1) IS NOT NULL
                ''')
                cursor.execute('DROP TABLE folios')
                cursor.execute('ALTER TABLE folios_new RENAME TO folios')
                conn.commit()
        finally:
            conn.close()

    def _revert_notes_tasks_linkage(self):
        """Reverts notes and tasks tables to link only to clients."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Revert Notes
            cursor.execute("PRAGMA table_info(notes)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'can_id' in columns:
                cursor.execute("""
                    UPDATE notes 
                    SET client_id = (SELECT client_id FROM client_cans WHERE id = notes.can_id)
                    WHERE client_id IS NULL AND can_id IS NOT NULL
                """)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notes_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        content TEXT NOT NULL,
                        category TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (client_id) REFERENCES clients (client_id)
                    )
                ''')
                cursor.execute('''
                    INSERT INTO notes_new (id, client_id, content, category, created_at)
                    SELECT id, client_id, content, category, created_at FROM notes
                ''')
                cursor.execute("DROP TABLE notes")
                cursor.execute("ALTER TABLE notes_new RENAME TO notes")

            # Revert Tasks
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'can_id' in columns:
                cursor.execute("""
                    UPDATE tasks 
                    SET client_id = (SELECT client_id FROM client_cans WHERE id = tasks.can_id)
                    WHERE client_id IS NULL AND can_id IS NOT NULL
                """)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        description TEXT NOT NULL,
                        due_date DATE,
                        status TEXT DEFAULT 'Pending',
                        priority TEXT DEFAULT 'Med',
                        FOREIGN KEY (client_id) REFERENCES clients (client_id)
                    )
                ''')
                cursor.execute('''
                    INSERT INTO tasks_new (id, client_id, description, due_date, status, priority)
                    SELECT id, client_id, description, due_date, status, priority FROM tasks
                ''')
                cursor.execute("DROP TABLE tasks")
                cursor.execute("ALTER TABLE tasks_new RENAME TO tasks")
            
            conn.commit()
        finally:
            conn.close()

    def _enforce_can_uniqueness(self):
        """Enforces uniqueness on can_number in client_cans table."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA index_list(client_cans)")
            indexes = cursor.fetchall()
            has_unique = any(idx[2] == 1 for idx in indexes) 
            
            if not has_unique:
                cursor.execute("""
                    DELETE FROM client_cans 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM client_cans 
                        GROUP BY can_number
                    )
                """)
                cursor.execute("ALTER TABLE client_cans RENAME TO client_cans_old")
                cursor.execute('''
                    CREATE TABLE client_cans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        can_number TEXT NOT NULL UNIQUE,
                        can_description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (client_id) REFERENCES clients (client_id)
                    )
                ''')
                cursor.execute('''
                    INSERT INTO client_cans (id, client_id, can_number, can_description, created_at)
                    SELECT id, client_id, can_number, can_description, created_at FROM client_cans_old
                ''')
                cursor.execute("DROP TABLE client_cans_old")
                conn.commit()
        finally:
            conn.close()

    def _rename_isin_code_to_scheme_code(self):
        """Migration: Renames isin_code column to scheme_code in schemes table."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(schemes)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'isin_code' in columns and 'scheme_code' not in columns:
                cursor.execute("ALTER TABLE schemes RENAME TO schemes_old")
                cursor.execute('''
                    CREATE TABLE schemes (
                        scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scheme_code TEXT UNIQUE,
                        rta_code TEXT,
                        scheme_name TEXT NOT NULL,
                        category TEXT,
                        current_nav REAL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    INSERT INTO schemes (scheme_id, scheme_code, scheme_name, category, current_nav, last_updated)
                    SELECT scheme_id, isin_code, scheme_name, category, current_nav, last_updated FROM schemes_old
                ''')
                cursor.execute("DROP TABLE schemes_old")
                conn.commit()
        finally:
            conn.close()

    def _add_rta_code_to_schemes(self):
        """Migration: Adds rta_code column to schemes table."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(schemes)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'rta_code' not in columns:
                cursor.execute("ALTER TABLE schemes ADD COLUMN rta_code TEXT")
            conn.commit()
        finally:
            conn.close()

    def _add_order_number_to_transactions(self):
        """Migration: Adds order_number column to transactions table."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'order_number' not in columns:
                cursor.execute("ALTER TABLE transactions ADD COLUMN order_number TEXT")
            conn.commit()
        finally:
            conn.close()
