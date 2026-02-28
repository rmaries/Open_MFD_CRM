import base64
import os
from src.modules.db.encryption import EncryptionMixin

def test_kdf():
    password = "super_secret_password"
    salt = os.urandom(16)
    
    key1 = EncryptionMixin.derive_key(password, salt)
    key2 = EncryptionMixin.derive_key(password, salt)
    
    print(f"Key 1: {key1}")
    print(f"Key 2: {key2}")
    
    assert key1 == key2, "Same password and salt should produce same key"
    
    other_password = "wrong_password"
    key3 = EncryptionMixin.derive_key(other_password, salt)
    assert key1 != key3, "Different password should produce different key"
    
    other_salt = os.urandom(16)
    key4 = EncryptionMixin.derive_key(password, other_salt)
    assert key1 != key4, "Different salt should produce different key"
    
    print("KDF logic verified successfully!")

if __name__ == "__main__":
    test_kdf()
