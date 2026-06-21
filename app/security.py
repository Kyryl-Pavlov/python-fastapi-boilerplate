import os
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import config

bearer = HTTPBearer(auto_error=False)  # auto_error=False lets us raise 401 instead of 403


def settings():
    name = os.environ.get("APP_ENV", "development")
    return config.get(name, config["default"])


def decode(token: str) -> dict:
    cfg = settings()
    return jwt.decode(token, cfg.JWT_SECRET_KEY, algorithms=[cfg.JWT_ALGORITHM])


def create_access_token(identity: str) -> str:
    cfg = settings()
    expires = timedelta(seconds=cfg.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    payload = {
        "sub": identity,
        "type": "access",
        "exp": datetime.now(UTC) + expires,
    }
    return jwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm=cfg.JWT_ALGORITHM)


def create_refresh_token(identity: str) -> str:
    cfg = settings()
    expires = timedelta(seconds=cfg.JWT_REFRESH_TOKEN_EXPIRES.total_seconds())
    payload = {
        "sub": identity,
        "type": "refresh",
        "exp": datetime.now(UTC) + expires,
    }
    return jwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm=cfg.JWT_ALGORITHM)


def verify_access_token(token: str) -> str:
    """Decode an access token and return the subject (user id). Raises on failure."""
    try:
        payload = decode(token)
    except JWTError as e:
        raise ValueError("Invalid or expired token") from e
    if payload.get("type") != "access":
        raise ValueError("Access token required")
    return payload["sub"]


def verify_refresh_token(token: str) -> str:
    """Decode a refresh token and return the subject. Raises on failure."""
    try:
        payload = decode(token)
    except JWTError as e:
        raise ValueError("Invalid or expired token") from e
    if payload.get("type") != "refresh":
        raise ValueError("Refresh token required")
    return payload["sub"]


def get_token_from_bearer(auth_header: str) -> str:
    """Extract raw JWT from 'Bearer <token>' string. Raises ValueError if malformed."""
    if not auth_header.startswith("Bearer "):
        raise ValueError("Missing or invalid Authorization header")
    return auth_header[len("Bearer "):]


# ── FastAPI dependency helpers ──────────────────────────────────────────────


def require_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    """Dependency: validates access token and returns user_id."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        return verify_access_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


def require_refresh_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    """Dependency: validates refresh token and returns user_id."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        return verify_refresh_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
