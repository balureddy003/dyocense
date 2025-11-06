"""Secure credential encryption for connector configurations."""

import os
import json
import logging
from typing import Any
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """
    Encrypts and decrypts connector credentials using Fernet (symmetric encryption).
    
    The encryption key should be stored securely in environment variables or a secrets manager.
    Never commit the key to version control.
    """
    
    def __init__(self, encryption_key: str | None = None):
        """
        Initialize encryption with a key.
        
        Args:
            encryption_key: Base64-encoded Fernet key. If None, reads from CONNECTOR_ENCRYPTION_KEY env var.
        """
        key = encryption_key or os.getenv("CONNECTOR_ENCRYPTION_KEY")
        
        if not key:
            # Generate a new key for development (NOT for production)
            logger.warning(
                "No CONNECTOR_ENCRYPTION_KEY found. Generating a temporary key. "
                "This is ONLY for development. Set CONNECTOR_ENCRYPTION_KEY in production!"
            )
            key = Fernet.generate_key().decode()
            logger.warning(f"Generated key: {key}")
            logger.warning("Store this key securely and set it in your environment variables!")
        
        try:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Invalid encryption key") from e
    
    def encrypt_config(self, config: dict[str, Any]) -> str:
        """
        Encrypt a configuration dictionary.
        
        Args:
            config: Dictionary containing connector configuration and credentials
            
        Returns:
            Base64-encoded encrypted string
        """
        try:
            config_json = json.dumps(config)
            encrypted = self.cipher.encrypt(config_json.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt configuration") from e
    
    def decrypt_config(self, encrypted_config: str) -> dict[str, Any]:
        """
        Decrypt a configuration string.
        
        Args:
            encrypted_config: Base64-encoded encrypted string
            
        Returns:
            Decrypted configuration dictionary
            
        Raises:
            ValueError: If decryption fails (invalid key or corrupted data)
        """
        try:
            decrypted = self.cipher.decrypt(encrypted_config.encode())
            config = json.loads(decrypted.decode())
            return config
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or corrupted data")
            raise ValueError("Failed to decrypt configuration: Invalid encryption key or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt configuration") from e
    
    def rotate_key(self, old_key: str, new_key: str, encrypted_data: str) -> str:
        """
        Re-encrypt data with a new key (for key rotation).
        
        Args:
            old_key: Previous encryption key
            new_key: New encryption key
            encrypted_data: Data encrypted with old key
            
        Returns:
            Data re-encrypted with new key
        """
        old_cipher = Fernet(old_key.encode())
        new_cipher = Fernet(new_key.encode())
        
        # Decrypt with old key
        decrypted = old_cipher.decrypt(encrypted_data.encode())
        
        # Re-encrypt with new key
        re_encrypted = new_cipher.encrypt(decrypted)
        return re_encrypted.decode()


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.
    
    Returns:
        Base64-encoded encryption key as string
    """
    key = Fernet.generate_key()
    return key.decode()


# Global encryption instance
_encryption_instance: CredentialEncryption | None = None


def get_encryption() -> CredentialEncryption:
    """Get or create the global encryption instance."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = CredentialEncryption()
    return _encryption_instance
