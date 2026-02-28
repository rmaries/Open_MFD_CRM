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
        This method ensures the foundational schema is in place.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Clients table: Stores information about individual clients/investors.
            # client_id: Primary key, unique identifier for each client.
            # name: Full name of the client.
            # pan: Permanent Account Number, unique identifier for tax purposes.
            # can_number: Consolidated Account Number (legacy, now moved to client_cans table).
            # email, phone: Contact information.
            # kyc_status: Boolean indicating if KYC (Know Your Customer) is completed.
            # pan_card_url: URL or path to the client's PAN card document.
            # onboarding_date: Timestamp when the client was added.
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
            
            # Folios table: Represents investment folios, linking to CANs.
            # folio_id: Primary key, unique identifier for each folio.
            # can_id: Foreign key referencing the client_cans table, linking a folio to a specific CAN.
            # folio_number: Unique identifier for the folio within an AMC.
            # amc_name: Asset Management Company name associated with the folio.
            # is_active: Boolean indicating if the folio is currently active.
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
            
            # Schemes table: Stores details about various mutual fund schemes.
            # scheme_id: Primary key, unique identifier for each scheme.
            # isin_code: International Securities Identification Number, unique for each scheme.
            # scheme_name: Official name of the mutual fund scheme.
            # category: Category of the scheme (e.g., Equity, Debt, Hybrid).
            # current_nav: Net Asset Value per unit of the scheme.
            # last_updated: Timestamp of the last NAV update.
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
            
            # Transactions table: Records all investment transactions (purchase, redemption, SIP, etc.).
            # trans_id: Primary key, unique identifier for each transaction.
            # folio_id: Foreign key referencing the folios table, linking a transaction to a specific folio.
            # scheme_id: Foreign key referencing the schemes table, linking a transaction to a specific scheme.
            # date: Date of the transaction.
            # type: Type of transaction (PURCHASE, REDEMPTION, SIP, STP, SWP).
            # amount: Monetary amount of the transaction.
            # units: Number of units involved in the transaction.
            # nav_at_purchase: NAV at the time of purchase/transaction.
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

            # Notes table: Stores general notes or remarks related to investors.
            # id: Primary key, unique identifier for each note.
            # investor_id: Foreign key referencing the clients table.
            # content: The actual text content of the note.
            # category: Category of the note (e.g., "Meeting", "Call", "Follow-up").
            # created_at: Timestamp when the note was created.
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

            # Tasks table: Manages tasks associated with investors.
            # id: Primary key, unique identifier for each task.
            # investor_id: Foreign key referencing the clients table.
            # description: Detailed description of the task.
            # due_date: Date by which the task should be completed.
            # status: Current status of the task (Pending, In Progress, Completed, Cancelled).
            # priority: Priority level of the task (High, Med, Low).
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

            # Documents table: Stores metadata about documents uploaded for clients.
            # doc_id: Primary key, unique identifier for each document record.
            # client_id: Foreign key referencing the clients table.
            # file_name: Original name of the uploaded file.
            # file_path: Storage path or URL of the document.
            # doc_type: Category or type of the document (e.g., "KYC", "Agreement", "Statement").
            # uploaded_at: Timestamp when the document record was created.
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

            # Client CANs table: Manages multiple Consolidated Account Numbers (CANs) per client.
            # id: Primary key, unique identifier for each CAN record.
            # client_id: Foreign key referencing the clients table, linking a CAN to a specific client.
            # can_number: The actual CAN number.
            # created_at: Timestamp when the CAN record was created.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS client_cans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    can_number TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients (client_id)
                )
            ''')
            
            conn.commit()
        finally:
            conn.close()

    def _run_migrations(self):
        """
        Executes one-time schema migrations to update the database structure
        or data based on application evolution.
        These migrations are designed to be idempotent.
        """
        self._migrate_cans_to_table()
        self._migrate_folios_to_cans()

    def _migrate_cans_to_table(self):
        """
        Migration: Moves legacy CAN numbers from the 'clients' table into the new 'client_cans' table.
        This ensures that CANs are managed as separate entities, allowing for multiple CANs per client.
        It runs only if the client_cans table is empty, preventing duplicate entries on subsequent runs.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            # Check if the client_cans table is empty to ensure idempotency
            cursor.execute("SELECT count(*) FROM client_cans")
            if cursor.fetchone()[0] == 0:
                # Select client_id and can_number from clients where can_number exists
                cursor.execute("SELECT client_id, can_number FROM clients WHERE can_number IS NOT NULL AND can_number != ''")
                existing_cans = cursor.fetchall()
                for client_id, can in existing_cans:
                    cursor.execute("INSERT INTO client_cans (client_id, can_number) VALUES (?, ?)", (client_id, can))
                conn.commit()
        finally:
            conn.close()

    def _migrate_folios_to_cans(self):
        """Adjusts folios table to link to CANs instead of directly to Clients if necessary."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(folios)")
            folio_cols = [row[1] for row in cursor.fetchall()]
            
            if 'client_id' in folio_cols and 'can_id' not in folio_cols:
                # This logic replicates the original migration in database.py
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
