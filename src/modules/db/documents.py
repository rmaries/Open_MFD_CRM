import os
from .connection import BaseRepository
from .encryption import EncryptionMixin

class DocumentRepository(EncryptionMixin, BaseRepository):
    """
    Encrypted file storage system. 
    Encrypts binary contents before saving to disk and manages DB metadata.
    """
    def __init__(self, db_path: str, key: str = None):
        """Initialize with DB path and file encryption support."""
        BaseRepository.__init__(self, db_path)
        EncryptionMixin.__init__(self, key)

    def add_document(self, client_id, file_obj, doc_type="Other"):
        """Encrypts and saves a physical file, then logs it in the DB."""
        base_dir = "data/documents"
        client_dir = os.path.join(base_dir, f"client_{client_id}")
        os.makedirs(client_dir, exist_ok=True)
        
        file_path = os.path.join(client_dir, file_obj.name)
        
        # Encrypt the binary blob using the master key
        plain_content = bytes(file_obj.getbuffer())
        encrypted_content = self.cipher.encrypt(plain_content)
        
        with open(file_path, "wb") as f:
            f.write(encrypted_content)
        
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
        """Reads and decrypts file content from the filesystem."""
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
            # Decrypt back into original binary format
            return self.cipher.decrypt(encrypted_content)
        except Exception:
            # Fallback for plain files if encryption was added to an existing data set
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
