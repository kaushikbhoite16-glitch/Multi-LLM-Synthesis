"""
Security utilities: Password hashing via PBKDF2-HMAC-SHA256 and JWT Token Management.
"""
import hashlib
import os
import hmac
import datetime
from typing import Optional, Dict, Any
import jwt
from app.config import settings

def hash_password(password: str) -> str:
    """Secure password hashing using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + dk.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Timing-safe password verification."""
    if not hashed_password or ":" not in hashed_password:
        return False
    parts = hashed_password.split(":")
    if len(parts) != 2:
        return False
    try:
        salt = bytes.fromhex(parts[0])
        expected = bytes.fromhex(parts[1])
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generates signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def verify_google_id_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Google OAuth ID token using Google's official library.
    Strictly verifies:
      1. Cryptographic signature against Google's public certs
      2. Token expiration (exp)
      3. Token issuer (accounts.google.com or https://accounts.google.com)
      4. Audience (must match configured GOOGLE_CLIENT_ID if set)

    Raises ValueError if verification fails.
    """
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    transport = google_requests.Request()
    expected_audience = settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID.strip() else None

    # verify_oauth2_token validates signature, issuer, exp, and audience
    idinfo = id_token.verify_oauth2_token(token, transport, audience=expected_audience)

    # Confirm issuer is Google
    issuer = idinfo.get("iss", "")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError(f"Invalid token issuer: {issuer}")

    return idinfo

