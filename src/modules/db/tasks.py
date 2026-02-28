import pandas as pd
from .connection import BaseRepository
from .encryption import EncryptionMixin

class TaskRepository(EncryptionMixin, BaseRepository):
    """
    Workflow management for MFD tasks (KYC, reviews, etc.).
    """
    def __init__(self, db_path: str, key: str = None):
        BaseRepository.__init__(self, db_path)
        EncryptionMixin.__init__(self, key)

    def add_task(self, client_id=None, can_id=None, description="", due_date=None, status="Pending", priority="Med"):
        """Assigns a new task to a client profile or specific CAN."""
        # Ensure IDs are standard integers for SQLite compatibility
        cid = int(client_id) if client_id is not None else None
        canid = int(can_id) if can_id is not None else None
        
        query = 'INSERT INTO tasks (client_id, can_id, description, due_date, status, priority) VALUES (?, ?, ?, ?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (cid, canid, description, due_date, status, priority))
                return cursor.lastrowid
        finally:
            conn.close()

    def update_task_status(self, task_id, status):
        """Updates the progress status of a task."""
        query = 'UPDATE tasks SET status = ? WHERE id = ?'
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(query, (status, task_id))
        finally:
            conn.close()

    def get_tasks(self, client_id=None, can_id=None):
        """Returns tasks for a specific client/CAN or all pending tasks globally."""
        if can_id:
            query = 'SELECT * FROM tasks WHERE can_id = ? ORDER BY due_date ASC'
            return self.run_query(query, params=(int(can_id),))
        elif client_id:
            query = 'SELECT * FROM tasks WHERE client_id = ? ORDER BY due_date ASC'
            return self.run_query(query, params=(int(client_id),))
        else:
            query = """
                SELECT t.*, cc.can_number, c.name as client_name 
                FROM tasks t 
                LEFT JOIN clients c ON t.client_id = c.client_id 
                LEFT JOIN client_cans cc ON t.can_id = cc.id
                ORDER BY due_date ASC
            """
            df = self.run_query(query)
            if not df.empty:
                df['owner_name'] = df.apply(
                    lambda row: self._decrypt(row['can_number']) if pd.notnull(row['can_number']) else row['client_name'], 
                    axis=1
                )
            return df

    def get_overdue_tasks(self):
        """Identifies tasks past their due date that aren't closed."""
        query = """
            SELECT t.*, cc.can_number, c.name as client_name 
            FROM tasks t 
            LEFT JOIN clients c ON t.client_id = c.client_id 
            LEFT JOIN client_cans cc ON t.can_id = cc.id
            WHERE t.due_date < DATE('now') AND t.status NOT IN ('Completed', 'Cancelled')
        """
        df = self.run_query(query)
        if not df.empty:
            df['owner_name'] = df.apply(
                lambda row: self._decrypt(row['can_number']) if pd.notnull(row['can_number']) else row['client_name'], 
                axis=1
            )
        return df
