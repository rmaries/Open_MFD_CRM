import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class EncryptionMixin:
    """
    Provides field-level encryption/decryption capabilities.
    Uses a derived key (from password + salt) for Fernet operations.
    """
    def __init__(self, key: str = None):
        """
        Initializes the cipher with a provided key. 
        The key should be a base64-encoded bytes string derived from KDF.
        """
        if not key:
            # Fallback for transient or test instances if absolutely necessary,
            # but ideally the key is passed from the Database facade after derivation.
            key = os.getenv("FERNET_KEY") or Fernet.generate_key().decode()
        
        try:
            self.key = key.strip().encode() if isinstance(key, str) else key
            self.cipher = Fernet(self.key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key provided. {e}")

    @staticmethod
    def derive_key(password: str, salt: bytes) -> str:
        """
        Derives a 32-byte key from a password and salt using PBKDF2.
        Returns a URL-safe base64-encoded string compatible with Fernet.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()

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
