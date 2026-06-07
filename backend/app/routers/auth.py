"""Authentication for a PRIVATE league.

  Nobody self-registers. The admin invites people by email; the invitee
  clicks a signed link to set a password. Login is email + password.
  Password resets / changes are OTP-driven (code emailed to the address).

  POST /auth/login            email + password → JWT
  GET  /auth/invite-info      ?token=…  → who the invite is for (for the UI)
  POST /auth/accept-invite    token + password → activates account, JWT
  POST /auth/forgot-password  email → emails a one-time code
  POST /auth/reset-password   email + code + new_password → JWT
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from ..core.config import settings
from ..core.db import get_session
from ..core.email_otp import generate_otp, hash_otp, send_otp
from ..core.security import create_access_token, decode_token
from ..models import OtpCode, User
from ..services.auth_service import hash_password, validate_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class AcceptInviteIn(BaseModel):
    token: str
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    email: EmailStr
    code: str
    new_password: str


def _token_response(user: User) -> dict:
    return {
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email,
                 "display_name": user.display_name, "balance": user.balance,
                 "is_admin": user.is_admin},
    }


@router.post("/login")
def login(payload: LoginIn, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email.lower())).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user.status == "disabled":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled — contact the admin")
    if user.status == "invited" or not user.password_hash:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Set your password first (use your invite link or 'Forgot password')")
    return _token_response(user)


@router.get("/invite-info")
def invite_info(token: str, session: Session = Depends(get_session)):
    try:
        payload = decode_token(token)
    except (JWTError, HTTPException):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This invite link is invalid or expired")
    if payload.get("type") != "invite":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not an invite link")
    user = session.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite no longer valid")
    return {"email": user.email, "display_name": user.display_name,
            "already_active": bool(user.password_hash)}


@router.post("/accept-invite")
def accept_invite(payload: AcceptInviteIn, session: Session = Depends(get_session)):
    try:
        decoded = decode_token(payload.token)
    except (JWTError, HTTPException):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This invite link is invalid or expired")
    if decoded.get("type") != "invite":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not an invite link")
    err = validate_password(payload.password)
    if err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, err)
    user = session.get(User, int(decoded["sub"]))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite no longer valid")
    user.password_hash = hash_password(payload.password)
    user.status = "active"
    session.add(user)
    session.commit()
    session.refresh(user)
    return _token_response(user)


@router.post("/forgot-password")
def forgot_password(payload: ForgotIn, session: Session = Depends(get_session)):
    email = payload.email.lower()
    user = session.exec(select(User).where(User.email == email)).first()
    # Always report success (don't leak which emails exist), but only send
    # to real, non-disabled accounts.
    resp: dict = {"sent": True, "ttl_minutes": settings.otp_ttl_minutes}
    if user and user.status != "disabled":
        code = generate_otp()
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_ttl_minutes)
        session.add(OtpCode(email=email, code_hash=hash_otp(code), expires_at=expires))
        session.commit()
        try:
            emailed = send_otp(email, code)
        except Exception:  # noqa: BLE001 — bad SMTP config must not 500 the user
            logging.getLogger("golazo.auth").exception("OTP email send failed")
            emailed = False
        if not emailed and settings.dev_echo_otp:
            resp["dev_otp"] = code
    return resp


@router.post("/reset-password")
def reset_password(payload: ResetIn, session: Session = Depends(get_session)):
    email = payload.email.lower()
    err = validate_password(payload.new_password)
    if err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, err)
    now = datetime.now(timezone.utc)
    otp = session.exec(
        select(OtpCode).where(OtpCode.email == email, OtpCode.consumed == False)  # noqa: E712
        .order_by(OtpCode.created_at.desc())).first()
    if not otp:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Request a code first")
    exp = otp.expires_at if otp.expires_at.tzinfo else otp.expires_at.replace(tzinfo=timezone.utc)
    if now > exp:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code expired")
    if otp.attempts >= 5:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts")
    if otp.code_hash != hash_otp(payload.code.strip()):
        otp.attempts += 1
        session.add(otp); session.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid code")
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    otp.consumed = True
    user.password_hash = hash_password(payload.new_password)
    if user.status == "invited":
        user.status = "active"
    session.add(otp); session.add(user)
    session.commit()
    session.refresh(user)
    return _token_response(user)
