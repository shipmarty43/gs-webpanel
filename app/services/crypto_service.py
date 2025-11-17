"""Cryptography service for encrypting/decrypting gsocket secrets"""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import settings


class CryptoService:
    """Service for encrypting and decrypting sensitive data"""

    def __init__(self):
        self.fernet = self._initialize_fernet()

    def _initialize_fernet(self) -> Fernet:
        """Initialize Fernet cipher with encryption key"""
        # Derive a proper key from the encryption key setting
        key = settings.ENCRYPTION_KEY.encode()

        # Use PBKDF2HMAC to derive a 32-byte key if needed
        if len(key) != 44:  # Fernet keys are 44 bytes when base64 encoded
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'gsocket-c2-salt',  # Static salt for consistency
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key))
        else:
            derived_key = key

        return Fernet(derived_key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string

        Args:
            plaintext: String to encrypt

        Returns:
            Base64 encoded encrypted string
        """
        if not plaintext:
            return ""

        encrypted = self.fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string

        Args:
            ciphertext: Base64 encoded encrypted string

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""

        try:
            encrypted = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt: {e}")


# Singleton instance
crypto_service = CryptoService()
