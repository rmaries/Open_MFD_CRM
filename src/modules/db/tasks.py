import pandas as pd
from .connection import BaseRepository


class TaskRepository(BaseRepository):
    """
    Workflow management for MFD tasks (KYC, reviews, etc.).
    """
    def __init__(self, db_path: str):
        BaseRepository.__init__(self, db_path)

    def add_task(self, client_id, description="", due_date=None, status="Pending", priority="Med"):
        """Assigns a new task to a client profile."""
        # Ensure ID is standard integer for SQLite compatibility
        cid = int(client_id) if client_id is not None else None
        
        query = 'INSERT INTO tasks (client_id, description, due_date, status, priority) VALUES (?, ?, ?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (cid, description, due_date, status, priority))
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

    def get_tasks(self, client_id=None):
        """Returns tasks for a specific client or all pending tasks globally."""
        if client_id:
            query = 'SELECT * FROM tasks WHERE client_id = ? ORDER BY due_date ASC'
            return self.run_query(query, params=(int(client_id),))
        else:
            query = """
                SELECT t.*, c.name as client_name 
                FROM tasks t 
                LEFT JOIN clients c ON t.client_id = c.client_id 
                ORDER BY due_date ASC
            """
            df = self.run_query(query)
            if not df.empty:
                df['owner_name'] = df['client_name']
            return df

    def get_overdue_tasks(self):
        """Identifies tasks past their due date that aren't closed."""
        query = """
            SELECT t.*, c.name as client_name 
            FROM tasks t 
            LEFT JOIN clients c ON t.client_id = c.client_id 
            WHERE t.due_date < DATE('now') AND t.status NOT IN ('Completed', 'Cancelled')
        """
        df = self.run_query(query)
        if not df.empty:
            df['owner_name'] = df['client_name']
        return df
