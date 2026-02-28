import os
from dotenv import load_dotenv
from .schema import SchemaManager
from .clients import ClientRepository
from .folios import FolioRepository
from .transactions import TransactionRepository
from .notes import NoteRepository
from .tasks import TaskRepository
from .documents import DocumentRepository

# Load environment variables
load_dotenv()

class Database:
    """
    Facade class that composes all modularized repositories.
    Stores all data in plain text.
    """
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv("DB_PATH", "open_mfd.db")
        self.db_path = db_path
        
        # Initialize Sub-Repositories
        self.schema = SchemaManager(db_path)
        self.clients = ClientRepository(db_path)
        self.folios = FolioRepository(db_path)
        self.transactions = TransactionRepository(db_path)
        self.notes = NoteRepository(db_path)
        self.tasks = TaskRepository(db_path)
        self.documents = DocumentRepository(db_path)
        
        # Initialize database schema
        self.schema.init_db()

    # --- Schema/Connection Passthroughs ---
    def get_connection(self):
        return self.schema.get_connection()

    def run_query(self, query, params=None):
        return self.schema.run_query(query, params)

    # --- Client Passthroughs ---
    def add_client(self, *args, **kwargs):
        return self.clients.add_client(*args, **kwargs)

    def get_all_clients(self):
        return self.clients.get_all_clients()

    def get_client_info(self, client_id):
        return self.clients.get_client_info(client_id)

    def update_client_info(self, *args, **kwargs):
        return self.clients.update_client_info(*args, **kwargs)

    def update_client_kyc(self, client_id, status):
        return self.clients.update_client_kyc(client_id, status)

    def add_client_can(self, client_id, can, can_description=None):
        return self.clients.add_client_can(client_id, can, can_description=can_description)

    def get_client_cans(self, client_id):
        return self.clients.get_client_cans(client_id)

    def delete_client_can(self, can_id):
        return self.clients.delete_client_can(can_id)

    # --- Folio Passthroughs ---
    def add_folio(self, *args, **kwargs):
        return self.folios.add_folio(*args, **kwargs)

    def get_folios_for_can(self, can_id):
        return self.folios.get_folios_for_can(can_id)

    # --- Transaction Passthroughs ---
    def add_transaction(self, *args, **kwargs):
        return self.transactions.add_transaction(*args, **kwargs)

    def get_client_portfolio(self, client_id, can_id=None):
        return self.transactions.get_client_portfolio(client_id, can_id=can_id)

    def get_total_metrics(self):
        return self.transactions.get_total_metrics()
        
    def get_transactions_for_calculations(self, client_id, can_id=None):
        return self.transactions.get_transactions_for_calculations(client_id, can_id=can_id)

    # --- Note Passthroughs ---
    def add_note(self, *args, **kwargs):
        return self.notes.add_note(*args, **kwargs)

    def get_notes(self, client_id):
        return self.notes.get_notes(client_id)

    def search_notes(self, keyword):
        return self.notes.search_notes(keyword)

    # --- Task Passthroughs ---
    def add_task(self, *args, **kwargs):
        return self.tasks.add_task(*args, **kwargs)

    def update_task_status(self, task_id, status):
        return self.tasks.update_task_status(task_id, status)

    def get_tasks(self, client_id=None):
        return self.tasks.get_tasks(client_id)

    def get_overdue_tasks(self):
        return self.tasks.get_overdue_tasks()

    # --- Document Passthroughs ---
    def add_document(self, *args, **kwargs):
        return self.documents.add_document(*args, **kwargs)

    def get_documents(self, client_id):
        return self.documents.get_documents(client_id)

    def get_document_content(self, doc_id):
        return self.documents.get_document_content(doc_id)

    def delete_document(self, doc_id):
        return self.documents.delete_document(doc_id)
