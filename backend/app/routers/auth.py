from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..config import settings
from ..services.auth import authenticate, issue_token, require_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    token: str
    role: str
    username: str
    auth_enabled: bool


@router.post("/login", response_model=LoginOut)
async def login(body: LoginIn) -> LoginOut:
    if not settings.AUTH_ENABLED:
        return LoginOut(token="", role="admin", username=body.username or "anonymous", auth_enabled=False)
    res = authenticate(body.username, body.password)
    if not res:
        raise HTTPException(401, "Invalid credentials")
    username, role = res
    return LoginOut(token=issue_token(username, role), role=role, username=username, auth_enabled=True)


@router.get("/me")
async def me(user: dict = Depends(require_user)) -> dict:
    return {"username": user.get("sub"), "role": user.get("role"), "auth_enabled": settings.AUTH_ENABLED}


@router.get("/config")
async def auth_config() -> dict:
    """Public endpoint so the frontend knows whether to show a login screen."""
    return {"auth_enabled": settings.AUTH_ENABLED}
