"""Admin console API: invite/manage players, enter results, run sims.
All endpoints require an admin JWT."""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from ..core.config import settings
from ..core.db import get_session
from ..core import email_otp
from ..core.email_otp import send_invite
from ..core.security import create_invite_token, current_user_id
from ..models import Bet, LedgerEntry, Match, Team, User
from ..quant.poisson import lambdas
from ..services import (
    betting_service, market_service, settings_service, sim_service, url_shortener,
)

router = APIRouter(prefix="/admin", tags=["admin"])
_rng = np.random.default_rng()


def require_admin(uid: int = Depends(current_user_id),
                  session: Session = Depends(get_session)) -> User:
    user = session.get(User, uid)
    if not user or not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user


# ── users ──────────────────────────────────────────────────────────────

class InviteIn(BaseModel):
    email: EmailStr
    display_name: str | None = None
    is_admin: bool = False


def _invite_link(user: User) -> str:
    token = create_invite_token(str(user.id), user.email)
    full = f"{settings.public_base_url.rstrip('/')}/accept-invite?token={token}"
    return url_shortener.shorten(full)


def _user_row(u: User, session: Session) -> dict:
    bets = session.exec(select(Bet).where(Bet.user_id == u.id)).all()
    return {
        "id": u.id, "email": u.email, "display_name": u.display_name,
        "status": u.status, "is_admin": u.is_admin, "balance": u.balance,
        "bets": len(bets), "has_password": bool(u.password_hash),
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.post("/users/invite")
def invite_user(payload: InviteIn, admin: User = Depends(require_admin),
                session: Session = Depends(get_session)):
    email = payload.email.lower().strip()
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing and existing.password_hash:
        raise HTTPException(status.HTTP_409_CONFLICT, "user already active")
    if existing:
        user = existing
        if payload.display_name:
            user.display_name = payload.display_name
        user.is_admin = user.is_admin or payload.is_admin
    else:
        user = User(email=email,
                    display_name=(payload.display_name or email.split("@")[0]).strip()[:40],
                    balance=settings.starting_balance, is_admin=payload.is_admin,
                    status="invited", invited_by=admin.email)
        session.add(user)
        session.commit()
        session.refresh(user)
        session.add(LedgerEntry(user_id=user.id, kind="signup",
                                amount=settings.starting_balance,
                                balance_after=user.balance, memo="welcome bonus"))
    session.add(user)
    session.commit()
    session.refresh(user)
    link = _invite_link(user)
    emailed = _safe_send_invite(user, link, admin.display_name)
    resp = {"user": _user_row(user, session), "emailed": emailed}
    if not emailed:                      # email off/failed → let admin copy the link
        resp["invite_link"] = link
    return resp


def _safe_send_invite(user: User, link: str, inviter: str) -> bool:
    try:
        return send_invite(user.email, user.display_name, link, inviter)
    except Exception:  # noqa: BLE001 — bad SMTP must not 500; admin shares link
        import logging
        logging.getLogger("golazo.admin").exception("invite email send failed")
        return False


@router.post("/users/{user_id}/resend-invite")
def resend_invite(user_id: int, admin: User = Depends(require_admin),
                  session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    link = _invite_link(user)
    emailed = _safe_send_invite(user, link, admin.display_name)
    resp = {"emailed": emailed}
    if not emailed:
        resp["invite_link"] = link
    return resp


@router.get("/users")
def list_users(_admin: User = Depends(require_admin), session: Session = Depends(get_session)):
    users = session.exec(select(User).order_by(User.created_at)).all()
    return [_user_row(u, session) for u in users]


class StatusIn(BaseModel):
    status: str  # active | disabled


@router.post("/users/{user_id}/status")
def set_status(user_id: int, body: StatusIn, _admin: User = Depends(require_admin),
               session: Session = Depends(get_session)):
    if body.status not in ("active", "disabled"):
        raise HTTPException(400, "status must be active or disabled")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    user.status = body.status
    session.add(user); session.commit()
    return _user_row(user, session)


class AdminFlagIn(BaseModel):
    is_admin: bool


@router.post("/users/{user_id}/admin")
def set_admin(user_id: int, body: AdminFlagIn, admin: User = Depends(require_admin),
              session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    if user.id == admin.id and not body.is_admin:
        raise HTTPException(400, "can't remove your own admin rights")
    user.is_admin = body.is_admin
    session.add(user); session.commit()
    return _user_row(user, session)


class GrantIn(BaseModel):
    amount: int


@router.post("/users/{user_id}/grant")
def grant_coins(user_id: int, body: GrantIn, _admin: User = Depends(require_admin),
                session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    user.balance += body.amount
    session.add(LedgerEntry(user_id=user.id, kind="bonus", amount=body.amount,
                            balance_after=user.balance, memo="admin grant"))
    session.add(user); session.commit()
    return _user_row(user, session)


# ── overview ───────────────────────────────────────────────────────────

@router.get("/overview")
def overview(_admin: User = Depends(require_admin), session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    matches = session.exec(select(Match)).all()
    bets = session.exec(select(Bet)).all()
    return {
        "users": {"total": len(users),
                  "active": sum(u.status == "active" for u in users),
                  "invited": sum(u.status == "invited" for u in users),
                  "disabled": sum(u.status == "disabled" for u in users),
                  "admins": sum(u.is_admin for u in users)},
        "matches": {"total": len(matches),
                    "finished": sum(m.status == "finished" for m in matches),
                    "scheduled": sum(m.status == "scheduled" for m in matches)},
        "bets": {"total": len(bets),
                 "open": sum(b.status == "open" for b in bets),
                 "coins_in_play": sum(b.stake for b in bets if b.status == "open")},
    }


# ── email / SMTP settings ──────────────────────────────────────────────

class SmtpIn(BaseModel):
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None   # blank = leave unchanged
    smtp_from: str | None = None


class TestEmailIn(BaseModel):
    to: EmailStr | None = None


@router.get("/settings")
def get_settings(_admin: User = Depends(require_admin)):
    return settings_service.get_smtp_public()


@router.post("/settings")
def save_settings(body: SmtpIn, _admin: User = Depends(require_admin)):
    return settings_service.set_smtp(body.model_dump(exclude_none=True))


@router.post("/settings/test-email")
def test_email(body: TestEmailIn, admin: User = Depends(require_admin)):
    to = (body.to or admin.email)
    try:
        ok = email_otp.send_test(to)
    except Exception as exc:  # noqa: BLE001 — surface SMTP error to the panel
        return {"ok": False, "message": f"{type(exc).__name__}: {exc}"}
    return {"ok": ok, "message": f"Test email sent to {to}" if ok
            else "No SMTP host configured yet."}


# ── results / settlement ───────────────────────────────────────────────

class Result(BaseModel):
    home_goals: int
    away_goals: int


@router.post("/matches/{match_id}/settle")
def settle(match_id: int, body: Result, _admin: User = Depends(require_admin),
           session: Session = Depends(get_session)):
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(404, "match not found")
    if not match.home_code or not match.away_code:
        raise HTTPException(400, "participants not set")
    return betting_service.settle_match(session, match, body.home_goals, body.away_goals)


@router.post("/matches/{match_id}/auto-settle")
def auto_settle(match_id: int, _admin: User = Depends(require_admin),
                session: Session = Depends(get_session)):
    """Draw a scoreline from the model and settle — for demos."""
    match = session.get(Match, match_id)
    if not match or not match.home_code or not match.away_code:
        raise HTTPException(404, "match/participants not available")
    h = session.exec(select(Team).where(Team.code == match.home_code)).first()
    a = session.exec(select(Team).where(Team.code == match.away_code)).first()
    ha = market_service.home_advantage(h, a)
    lh, la = lambdas(h.elo, a.elo, ha)
    hg, ag = int(_rng.poisson(lh)), int(_rng.poisson(la))
    return betting_service.settle_match(session, match, hg, ag)
