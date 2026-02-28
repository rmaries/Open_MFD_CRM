import os
from .connection import BaseRepository

class DocumentRepository(BaseRepository):
    """
    Plain-text file storage system. 
    Saves binary contents directly to disk and manages DB metadata.
    """
    def __init__(self, db_path: str, **kwargs):
        """Initialize with DB path."""
        BaseRepository.__init__(self, db_path)

    def add_document(self, client_id, file_obj, doc_type="Other"):
        """Saves a physical file directly, then logs it in the DB."""
        base_dir = "data/documents"
        client_dir = os.path.join(base_dir, f"client_{client_id}")
        os.makedirs(client_dir, exist_ok=True)
        
        file_path = os.path.join(client_dir, file_obj.name)
        
        # Save the binary blob directly
        content = bytes(file_obj.getbuffer())
        with open(file_path, "wb") as f:
            f.write(content)
        
        query = 'INSERT INTO documents (client_id, file_name, file_path, doc_type) VALUES (?, ?, ?, ?)'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (client_id, file_obj.name, file_path, doc_type))
                return cursor.lastrowid
        finally:
            conn.close()

    def get_document_content(self, doc_id) -> bytes | None:
        """Reads file content from the filesystem."""
        query = "SELECT file_path FROM documents WHERE doc_id = ?"
        df = self.run_query(query, params=(doc_id,))
        if df.empty:
            return None
        
        file_path = df.iloc[0]['file_path']
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, "rb") as f:
            return f.read()

    def get_documents(self, client_id):
        """Lists metadata for all documents owned by a client."""
        query = "SELECT * FROM documents WHERE client_id = ? ORDER BY uploaded_at DESC"
        return self.run_query(query, params=(client_id,))

    def delete_document(self, doc_id):
        """Deletes a document from both disk and database."""
        query = "SELECT file_path FROM documents WHERE doc_id = ?"
        df = self.run_query(query, params=(doc_id,))
        if df.empty:
            return False
        
        file_path = df.iloc[0]['file_path']
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
            
        conn = self.get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
                return True
        finally:
            conn.close()
