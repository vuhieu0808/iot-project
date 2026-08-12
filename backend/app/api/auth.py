"""JWT Authentication helper and FastAPI dependency for Admin & User routes."""

import hashlib
import time
import jwt
from typing import Optional
from fastapi import Header, HTTPException, status
from app.config import settings

ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 86400 * 7  # 7 days
SALT = "gymtag_salt_2026"


def hash_password(password: str) -> str:
    """Hash plain text password with sha256 + salt."""
    salted = f"{password}{SALT}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """Verify plain password against stored hash (or default '123456' / card_id fallback)."""
    if not hashed_password:
        # Default fallback for uninitialized passwords: '123456'
        return plain_password == "123456"
    return hash_password(plain_password) == hashed_password


def create_admin_token(username: str) -> str:
    """Generate a JWT token for authenticated admin."""
    payload = {
        "sub": username,
        "role": "admin",
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def verify_admin_token(token: str) -> Optional[str]:
    """Verify JWT token and return admin username if valid, else None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return None
        return payload.get("sub")
    except (jwt.PyJWTError, Exception):
        return None


def create_user_token(card_id: str) -> str:
    """Generate a JWT token for authenticated member (user)."""
    payload = {
        "sub": card_id,
        "role": "user",
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def verify_user_token(token: str) -> Optional[str]:
    """Verify JWT token and return member card_id if valid, else None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get("role") != "user":
            return None
        return payload.get("sub")
    except (jwt.PyJWTError, Exception):
        return None


def _get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1]


async def require_admin(authorization: Optional[str] = Header(None)) -> str:
    """FastAPI Dependency enforcing Bearer Admin JWT token authorization."""
    token = _get_bearer_token(authorization)
    username = verify_admin_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


async def require_user(authorization: Optional[str] = Header(None)) -> str:
    """FastAPI Dependency enforcing Bearer User JWT token authorization. Returns card_id."""
    token = _get_bearer_token(authorization)
    card_id = verify_user_token(token)
    if not card_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired user authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return card_id
