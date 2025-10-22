"""Encryption utilities for sensitive data like SII passwords.

Uses Fernet (symmetric encryption with AES-128-CBC + HMAC) to encrypt/decrypt
sensitive credentials. The encryption key is derived from SUPABASE_JWT_SECRET
using HKDF (HMAC-based Key Derivation Function) to ensure cryptographic separation.
"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def get_encryption_key() -> bytes:
    """
    Derive encryption key from SUPABASE_JWT_SECRET using HKDF.

    Uses HKDF to derive a separate 32-byte key for Fernet encryption from the
    existing JWT secret. This allows using the same secret for multiple purposes
    while maintaining cryptographic separation.

    Returns:
        URL-safe base64-encoded 32-byte key suitable for Fernet

    Raises:
        ValueError: If SUPABASE_JWT_SECRET is not set
    """
    jwt_secret = os.getenv('SUPABASE_JWT_SECRET')

    if not jwt_secret:
        raise ValueError(
            "SUPABASE_JWT_SECRET environment variable not set. "
            "This is required for password encryption."
        )

    # Use HKDF to derive a 32-byte key for Fernet
    # Fixed salt ensures consistent key derivation
    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'fizko-sii-password-encryption',  # Fixed salt for consistency
        info=b'sii-credentials',  # Context-specific info
    )

    # Derive key and encode for Fernet (requires URL-safe base64)
    derived_key = kdf.derive(jwt_secret.encode())
    return base64.urlsafe_b64encode(derived_key)


def encrypt_password(password: str) -> str:
    """
    Encrypt a plaintext password using Fernet.

    Args:
        password: The plaintext password to encrypt

    Returns:
        Base64-encoded encrypted password string

    Raises:
        ValueError: If password is None or empty
    """
    if not password:
        raise ValueError("Password cannot be None or empty")

    f = Fernet(get_encryption_key())
    encrypted_bytes = f.encrypt(password.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_password(encrypted: str) -> Optional[str]:
    """
    Decrypt an encrypted password using Fernet.

    Args:
        encrypted: The base64-encoded encrypted password

    Returns:
        Decrypted plaintext password, or None if encrypted is None/empty

    Raises:
        cryptography.fernet.InvalidToken: If decryption fails (wrong key or corrupted data)
    """
    if not encrypted:
        return None

    f = Fernet(get_encryption_key())
    decrypted_bytes = f.decrypt(encrypted.encode('utf-8'))
    return decrypted_bytes.decode('utf-8')
