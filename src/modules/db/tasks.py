from .connection import BaseRepository

class TaskRepository(BaseRepository):
    """
    Workflow management for MFD tasks (KYC, reviews, etc.).
    """
    def add_task(self, investor_id, description, due_date, status="Pending", priority="Med"):
        """Assigns a new task to a client profile."""
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
        """Updates the progress status of a task."""
        query = 'UPDATE tasks SET status = ? WHERE id = ?'
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(query, (status, task_id))
        finally:
            conn.close()

    def get_tasks(self, investor_id=None):
        """Returns tasks for a single investor or all pending tasks globally."""
        if investor_id:
            query = 'SELECT * FROM tasks WHERE investor_id = ? ORDER BY due_date ASC'
            return self.run_query(query, params=(investor_id,))
        else:
            query = "SELECT t.*, c.name as client_name FROM tasks t JOIN clients c ON t.investor_id = c.client_id ORDER BY due_date ASC"
            return self.run_query(query)

    def get_overdue_tasks(self):
        """Identifies tasks past their due date that aren't closed."""
        query = """
            SELECT t.*, c.name as client_name 
            FROM tasks t 
            JOIN clients c ON t.investor_id = c.client_id 
            WHERE t.due_date < DATE('now') AND t.status NOT IN ('Completed', 'Cancelled')
        """
        return self.run_query(query)
