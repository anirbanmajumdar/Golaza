"""XP / levels / badges / daily bonus / streaks — the game layer.

Levels follow a quadratic curve: reaching level L needs 100·(L−1)²  XP,
so each level is progressively harder (a classic RPG pacing). Badges are
one-shot achievements that also pay XP and a coin bonus. Everything here
is deliberately separate from the betting ledger so the *fun* economy and
the *forecasting-skill* economy can be ranked independently.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from ..models import Achievement, LedgerEntry, User

# code: (name, emoji, description, xp_reward, coin_reward)
BADGES: dict[str, tuple] = {
    "first_kick":     ("First Kick", "👟", "Place your first bet", 50, 200),
    "sharp_shooter":  ("Sharp Shooter", "🎯", "Place a positive-EV bet (your edge beats the model)", 80, 300),
    "giant_killer":   ("Giant Killer", "🗡️", "Win a bet on a <30% underdog", 150, 500),
    "hot_streak_3":   ("On Fire", "🔥", "Win 3 bets in a row", 120, 400),
    "hot_streak_5":   ("Unstoppable", "⚡", "Win 5 bets in a row", 250, 1000),
    "high_roller":    ("High Roller", "💰", "Stake 2,000+ on a single bet", 100, 0),
    "regular":        ("Season-Ticket Holder", "🎟️", "Place 25 bets", 200, 750),
    "oracle":         ("The Oracle", "🔮", "Positive Brier skill over 10+ settled bets", 300, 1500),
    "globe_trotter":  ("Globe Trotter", "🌍", "Bet on matches from 6+ different groups", 180, 600),
    "the_quant":      ("The Quant", "📈", "Run a tournament simulation", 60, 150),
}


def level_for_xp(xp: int) -> int:
    return int(math.floor(math.sqrt(max(0, xp) / 100.0))) + 1


def xp_for_level(level: int) -> int:
    return 100 * (level - 1) ** 2


def level_info(xp: int) -> dict:
    lvl = level_for_xp(xp)
    base = xp_for_level(lvl)
    nxt = xp_for_level(lvl + 1)
    span = max(1, nxt - base)
    return {
        "xp": xp,
        "level": lvl,
        "xp_into_level": xp - base,
        "xp_to_next": nxt - xp,
        "level_span": span,
        "progress": round((xp - base) / span, 3),
    }


def grant_xp(user: User, amount: int) -> None:
    user.xp += amount


def award_badge(session: Session, user: User, code: str) -> bool:
    """Idempotent. Returns True if newly awarded."""
    if code not in BADGES:
        return False
    existing = session.exec(
        select(Achievement).where(Achievement.user_id == user.id,
                                  Achievement.code == code)).first()
    if existing:
        return False
    _name, _emoji, _desc, xp_reward, coin_reward = BADGES[code]
    session.add(Achievement(user_id=user.id, code=code))
    user.xp += xp_reward
    if coin_reward:
        user.balance += coin_reward
        session.add(LedgerEntry(user_id=user.id, kind="achievement",
                                amount=coin_reward, balance_after=user.balance,
                                memo=f"badge: {code}"))
    session.add(user)
    return True


def claim_daily_bonus(session: Session, user: User, amount: int) -> dict:
    now = datetime.now(timezone.utc)
    last = user.last_bonus_at
    if last is not None:
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if now - last < timedelta(hours=20):
            nxt = last + timedelta(hours=20)
            return {"claimed": False, "next_at": nxt.isoformat(),
                    "message": "Daily bonus already claimed."}
    user.balance += amount
    user.last_bonus_at = now
    session.add(LedgerEntry(user_id=user.id, kind="bonus", amount=amount,
                            balance_after=user.balance, memo="daily bonus"))
    session.add(user)
    session.commit()
    return {"claimed": True, "amount": amount, "balance": user.balance}


def badge_catalog() -> list[dict]:
    return [{"code": c, "name": n, "emoji": e, "description": d,
             "xp_reward": xp, "coin_reward": coin}
            for c, (n, e, d, xp, coin) in BADGES.items()]
