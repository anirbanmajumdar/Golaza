"""Idempotent seeding of teams + the 104-match calendar, and an optional
demo user. Runs on startup; only inserts what's missing."""

from __future__ import annotations

import logging

from sqlmodel import Session, select

from ..data.schedule_2026 import all_matches
from ..data.teams_2026 import all_teams
from ..models import LedgerEntry, Match, Team, User
from ..core.config import settings

log = logging.getLogger("golazo.seed")


def seed_teams(session: Session) -> int:
    existing = {t.code for t in session.exec(select(Team)).all()}
    added = 0
    for t in all_teams():
        if t["code"] in existing:
            continue
        session.add(Team(
            code=t["code"], name=t["name"], group=t["group"],
            confederation=t["confederation"], flag=t["flag"],
            elo=float(t["elo"]), elo_seed=float(t["elo"]),
            fifa_pts=int(t["fifa_pts"]), is_host=bool(t["is_host"]),
        ))
        added += 1
    session.commit()
    return added


def seed_matches(session: Session) -> int:
    existing = {m.ext_id for m in session.exec(select(Match)).all()}
    added = 0
    for m in all_matches():
        if m["ext_id"] in existing:
            continue
        session.add(Match(
            ext_id=m["ext_id"], stage=m["stage"],
            stage_label=m.get("stage_label"), group=m.get("group"),
            home_code=m.get("home_code"), away_code=m.get("away_code"),
            venue=m["venue"], kickoff=m["kickoff"], round_order=m["round_order"],
        ))
        added += 1
    session.commit()
    return added


def seed_admins(session: Session) -> None:
    """Bootstrap admin accounts (status active, no password). They set their
    initial password via 'Forgot password' (OTP to email)."""
    for email in settings.admin_emails:
        email = email.lower().strip()
        if not email:
            continue
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            if not existing.is_admin:
                existing.is_admin = True
                session.add(existing)
            continue
        u = User(email=email, display_name=email.split("@")[0],
                 balance=settings.starting_balance, is_admin=True, status="active")
        session.add(u)
        session.commit()
        session.refresh(u)
        session.add(LedgerEntry(user_id=u.id, kind="signup",
                                amount=settings.starting_balance,
                                balance_after=u.balance, memo="admin bootstrap"))
        log.info("seeded admin %s (set password via Forgot password)", email)
    session.commit()


def run_all(session: Session) -> None:
    nt = seed_teams(session)
    nm = seed_matches(session)
    seed_admins(session)
    log.info("seed complete (+%d teams, +%d matches)", nt, nm)
