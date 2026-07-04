"""Security helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

ALGORITHM = "HS256"
PASSWORD_ITERATIONS = 210_000
SALT_BYTES = 16


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    expire_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=30)
    )
    payload = {"sub": subject, "exp": expire_at}
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("utf-8")
    encoded_hash = base64.urlsafe_b64encode(derived).decode("utf-8")
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${encoded_salt}${encoded_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, iteration_str, encoded_salt, encoded_hash = hashed_password.split(
            "$",
            3,
        )
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("utf-8"))
        expected = base64.urlsafe_b64decode(encoded_hash.encode("utf-8"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            int(iteration_str),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, base64.binascii.Error):
        return False


def _credential_cipher() -> Fernet:
    key = hashlib.sha256(settings.jwt_secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_credential(value: str) -> str:
    """Encrypt a reversible integration credential for storage."""

    return _credential_cipher().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_credential(value: str | None) -> str | None:
    """Decrypt an integration credential without exposing invalid ciphertext."""

    if not value:
        return None
    try:
        return _credential_cipher().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None
