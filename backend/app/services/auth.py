"""Optional simple auth.

Enabled when AUTH_ENABLED=true in env. Issues HMAC-signed bearer tokens with role.
For production, swap for OIDC / Auth0 / Cognito etc.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import time
from typing import Optional
from fastapi import Header, HTTPException
from ..config import settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _sign(payload: dict) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(settings.AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(sig)}"


def issue_token(username: str, role: str, ttl_seconds: int = 8 * 3600) -> str:
    now = int(time.time())
    return _sign({"sub": username, "role": role, "iat": now, "exp": now + ttl_seconds})


def verify_token(token: str) -> dict:
    try:
        body, sig = token.split(".")
        expected = _b64(hmac.new(settings.AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError("Bad signature")
        payload = json.loads(_b64d(body))
        if payload.get("exp", 0) < int(time.time()):
            raise ValueError("Token expired")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}") from e


def require_user(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI dependency. Pass-through when AUTH_ENABLED=false."""
    if not settings.AUTH_ENABLED:
        return {"sub": "anonymous", "role": "admin"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return verify_token(authorization.split(" ", 1)[1])


# Demo users — replace with DB lookup in production
DEMO_USERS = {
    "admin": ("admin123", "admin"),
    "analyst": ("analyst123", "analyst"),
    "viewer": ("viewer123", "viewer"),
}


def authenticate(username: str, password: str) -> tuple[str, str] | None:
    rec = DEMO_USERS.get(username)
    if not rec:
        return None
    pw, role = rec
    if hmac.compare_digest(pw, password):
        return username, role
    return None
