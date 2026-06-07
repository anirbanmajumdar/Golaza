from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from jose import JWTError
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from ..core.config import settings
from ..core.db import get_session
from ..core.security import (
    create_access_token, create_league_invite_token, current_user_id, decode_token,
)
from ..models import Bet, LedgerEntry, League, LeagueMember, User
from ..quant.scoring import brier_skill_score
from ..services import gamification_service as gs
from ..services.auth_service import hash_password, validate_password, verify_password
from ..services.url_shortener import shorten

router = APIRouter(tags=["leaderboard"])

METRICS = {"balance", "net_profit", "skill", "level", "streak"}


def _rows(session: Session, user_ids: list[int] | None = None) -> list[dict]:
    q = select(User)
    if user_ids is not None:
        if not user_ids:
            return []
        q = q.where(User.id.in_(user_ids))
    users = session.exec(q).all()
    bets = session.exec(select(Bet)).all()
    by_user: dict[int, list[Bet]] = {}
    for b in bets:
        by_user.setdefault(b.user_id, []).append(b)
    rows = []
    for u in users:
        ub = by_user.get(u.id, [])
        settled = [b for b in ub if b.status in ("won", "lost")]
        staked = sum(b.stake for b in settled)
        returned = sum(b.payout for b in settled if b.status == "won")
        bss = (brier_skill_score(u.brier_sum, u.brier_ref_sum)
               if u.brier_count >= 5 else None)
        rows.append({
            "user_id": u.id, "display_name": u.display_name,
            "balance": u.balance,
            "net_profit": returned - staked,
            "level": gs.level_for_xp(u.xp), "xp": u.xp,
            "best_streak": u.best_streak, "current_streak": u.current_streak,
            "skill": round(bss, 4) if bss is not None else None,
            "bets_settled": len(settled),
        })
    return rows


def _sort(rows: list[dict], metric: str) -> list[dict]:
    keymap = {"balance": "balance", "net_profit": "net_profit",
              "skill": "skill", "level": "xp", "streak": "best_streak"}
    key = keymap[metric]
    rows = [r for r in rows if not (metric == "skill" and r["skill"] is None)]
    rows.sort(key=lambda r: (r[key] is not None, r[key]), reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


@router.get("/leaderboard")
def leaderboard(metric: str = Query("balance"), session: Session = Depends(get_session)):
    if metric not in METRICS:
        raise HTTPException(400, f"metric must be one of {sorted(METRICS)}")
    return {"metric": metric, "entries": _sort(_rows(session), metric)}


# ── leagues ──────────────────────────────────────────────────────────────

class CreateLeague(BaseModel):
    name: str


class JoinLeague(BaseModel):
    code: str


@router.post("/leagues")
def create_league(payload: CreateLeague, uid: int = Depends(current_user_id),
                  session: Session = Depends(get_session)):
    code = secrets.token_hex(3).upper()
    lg = League(name=payload.name.strip()[:60], join_code=code, owner_id=uid)
    session.add(lg)
    session.commit()
    session.refresh(lg)
    session.add(LeagueMember(league_id=lg.id, user_id=uid))
    session.commit()
    return {"id": lg.id, "name": lg.name, "join_code": lg.join_code}


@router.post("/leagues/join")
def join_league(payload: JoinLeague, uid: int = Depends(current_user_id),
                session: Session = Depends(get_session)):
    lg = session.exec(select(League).where(League.join_code == payload.code.upper())).first()
    if not lg:
        raise HTTPException(404, "no league with that code")
    exists = session.exec(select(LeagueMember).where(
        LeagueMember.league_id == lg.id, LeagueMember.user_id == uid)).first()
    if not exists:
        session.add(LeagueMember(league_id=lg.id, user_id=uid))
        session.commit()
    return {"id": lg.id, "name": lg.name, "join_code": lg.join_code}


# ── shareable league invite link (account + auto-join in one step) ──

class LeagueInviteAccept(BaseModel):
    token: str
    email: EmailStr
    display_name: str | None = None
    password: str


def _league_from_token(token: str, session: Session) -> League:
    try:
        decoded = decode_token(token)
    except (JWTError, HTTPException):
        raise HTTPException(400, "This invite link is invalid or expired")
    if decoded.get("type") != "league_invite":
        raise HTTPException(400, "Not a league invite link")
    lg = session.get(League, int(decoded["sub"]))
    if not lg:
        raise HTTPException(404, "League no longer exists")
    return lg


@router.get("/leagues/{league_id}/invite-link")
def league_invite_link(league_id: int, uid: int = Depends(current_user_id),
                       session: Session = Depends(get_session)):
    member = session.exec(select(LeagueMember).where(
        LeagueMember.league_id == league_id, LeagueMember.user_id == uid)).first()
    if not member:
        raise HTTPException(403, "join the league to share it")
    lg = session.get(League, league_id)
    token = create_league_invite_token(league_id)
    full = f"{settings.public_base_url.rstrip('/')}/join?token={token}"
    return {"link": shorten(full), "league": lg.name}


@router.get("/leagues/invite/info")
def league_invite_info(token: str, session: Session = Depends(get_session)):
    lg = _league_from_token(token, session)
    n = len(session.exec(select(LeagueMember).where(LeagueMember.league_id == lg.id)).all())
    return {"league": lg.name, "members": n}


@router.post("/leagues/invite/accept")
def league_invite_accept(payload: LeagueInviteAccept, session: Session = Depends(get_session)):
    lg = _league_from_token(payload.token, session)
    email = payload.email.lower().strip()
    user = session.exec(select(User).where(User.email == email)).first()

    if user and user.password_hash:
        # existing account → this doubles as login; verify their password
        if user.status == "disabled":
            raise HTTPException(403, "Account disabled — contact the admin")
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(401, "An account exists for this email — enter its password to join")
    else:
        err = validate_password(payload.password)
        if err:
            raise HTTPException(400, err)
        if user:  # invited but never set a password
            user.password_hash = hash_password(payload.password)
            user.status = "active"
            if payload.display_name:
                user.display_name = payload.display_name
        else:     # brand-new self-serve account, gated by the league link
            user = User(email=email,
                        display_name=(payload.display_name or email.split("@")[0]).strip()[:40],
                        password_hash=hash_password(payload.password),
                        status="active", balance=settings.starting_balance,
                        invited_by=f"league:{lg.name}")
            session.add(user); session.commit(); session.refresh(user)
            session.add(LedgerEntry(user_id=user.id, kind="signup",
                                    amount=settings.starting_balance,
                                    balance_after=user.balance, memo="welcome bonus"))
        session.add(user); session.commit(); session.refresh(user)

    if not session.exec(select(LeagueMember).where(
            LeagueMember.league_id == lg.id, LeagueMember.user_id == user.id)).first():
        session.add(LeagueMember(league_id=lg.id, user_id=user.id))
        session.commit()

    return {
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer",
        "league": {"id": lg.id, "name": lg.name},
        "user": {"id": user.id, "email": user.email,
                 "display_name": user.display_name, "balance": user.balance,
                 "is_admin": user.is_admin},
    }


@router.get("/leagues")
def my_leagues(uid: int = Depends(current_user_id), session: Session = Depends(get_session)):
    mems = session.exec(select(LeagueMember).where(LeagueMember.user_id == uid)).all()
    out = []
    for m in mems:
        lg = session.get(League, m.league_id)
        if not lg:
            continue
        n = len(session.exec(select(LeagueMember).where(
            LeagueMember.league_id == lg.id)).all())
        out.append({"id": lg.id, "name": lg.name, "join_code": lg.join_code,
                    "members": n, "is_owner": lg.owner_id == uid})
    return out


@router.get("/leagues/{league_id}")
def league_detail(league_id: int, metric: str = Query("balance"),
                  uid: int = Depends(current_user_id), session: Session = Depends(get_session)):
    lg = session.get(League, league_id)
    if not lg:
        raise HTTPException(404, "league not found")
    member_ids = [m.user_id for m in session.exec(
        select(LeagueMember).where(LeagueMember.league_id == league_id)).all()]
    if uid not in member_ids:
        raise HTTPException(403, "join the league to view it")
    metric = metric if metric in METRICS else "balance"
    return {"id": lg.id, "name": lg.name, "join_code": lg.join_code,
            "metric": metric, "entries": _sort(_rows(session, member_ids), metric)}
