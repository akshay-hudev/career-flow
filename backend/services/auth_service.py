"""
Authentication service
=======================
Password hashing (bcrypt via passlib) and JWT creation/validation (python-jose).
These helpers are imported by backend/routers/auth.py and backend/dependencies.py.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.models import User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# bcrypt only uses the first 72 bytes of a password, and bcrypt >= 5 raises
# instead of silently truncating — so we truncate explicitly. We call bcrypt
# directly rather than through passlib, which is unmaintained and crashes on
# bcrypt >= 5 (its backend probe hashes a >72-byte string at import time).
_BCRYPT_MAX_BYTES = 72


def _pw_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(_pw_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(_pw_bytes(plain_password), hashed_password.encode("utf-8"))
    except Exception:
        return False


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Return the user if the email exists and the password is correct, else None."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
