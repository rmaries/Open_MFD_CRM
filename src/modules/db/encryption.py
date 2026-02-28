import os
from cryptography.fernet import Fernet, InvalidToken

class EncryptionMixin:
    """
    Provides field-level encryption/decryption capabilities.
    Initializes a Fernet cipher based on the FERNET_KEY environment variable.
    """
    def __init__(self, key: str = None):
        if not key:
            key = os.getenv("FERNET_KEY")
        
        if not key:
            # For portable mode/fresh starts, we generate a key if missing
            key = Fernet.generate_key().decode()
        
        try:
            self.key = key.strip().encode()
            self.cipher = Fernet(self.key)
        except Exception as e:
            print(f"DEBUG: Invalid Fernet key: '{key}' (Length: {len(str(key))})")
            raise e

    def _encrypt(self, text: str) -> str | None:
        """Encrypts a string into a Fernet-encoded token."""
        if not text:
            return None
        return self.cipher.encrypt(str(text).encode()).decode()

    def _decrypt(self, encrypted_text: str) -> str | None:
        """
        Decrypts a token back to a string. 
        Falls back to returning the original text if decryption fails (e.g., for legacy plain data).
        """
        if not encrypted_text:
            return None
        try:
            return self.cipher.decrypt(str(encrypted_text).encode()).decode()
        except (InvalidToken, Exception):
            # Fallback for data migrated before encryption was standard
            return str(encrypted_text)
