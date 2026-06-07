"""JWT issuance + bearer dependency. OTP login means there is no password
to hash — identity is proven by the email round-trip, then a JWT carries
the session."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .config import settings

_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/verify", auto_error=False)


def create_access_token(sub: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_minutes)).timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_invite_token(sub: str, email: str) -> str:
    """Signed token embedded in the invite link. Proves email possession
    when the user clicks through to set their password."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.invite_ttl_hours)).timestamp()),
        "type": "invite",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_league_invite_token(league_id: int) -> str:
    """Long-lived signed token for a shareable league-join link. Anyone with
    the link can create an account (or sign in) and auto-join the league."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(league_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=30)).timestamp()),
        "type": "league_invite",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {exc}") from exc


def current_user_id(token: Annotated[str | None, Depends(_oauth2)]) -> int:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong token type")
    return int(payload["sub"])
