"""The signed-in user: profile, level, skill score, ledger, bets, daily
bonus, badges."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..core.config import settings
from ..core.db import get_session
from ..core.security import current_user_id
from ..models import Achievement, Bet, LedgerEntry, User
from ..quant.scoring import brier_skill_score
from ..services import gamification_service as gs

router = APIRouter(prefix="/me", tags=["me"])


def _profile(user: User, session: Session) -> dict:
    bets = session.exec(select(Bet).where(Bet.user_id == user.id)).all()
    settled = [b for b in bets if b.status in ("won", "lost")]
    won = [b for b in settled if b.status == "won"]
    staked = sum(b.stake for b in settled)
    returned = sum(b.payout for b in won)
    bss = brier_skill_score(user.brier_sum, user.brier_ref_sum) if user.brier_count else None
    return {
        "id": user.id, "email": user.email, "display_name": user.display_name,
        "avatar_seed": user.avatar_seed, "balance": user.balance,
        "is_admin": user.is_admin, "status": user.status,
        "level": gs.level_info(user.xp),
        "current_streak": user.current_streak, "best_streak": user.best_streak,
        "stats": {
            "bets_placed": len(bets),
            "bets_settled": len(settled),
            "bets_won": len(won),
            "hit_rate": round(len(won) / len(settled), 3) if settled else None,
            "coins_staked": staked,
            "net_profit": returned - staked,
            "roi": round((returned - staked) / staked, 3) if staked else None,
            "brier_count": user.brier_count,
            "brier_skill_score": round(bss, 4) if bss is not None else None,
        },
    }


@router.get("")
def me(uid: int = Depends(current_user_id), session: Session = Depends(get_session)):
    return _profile(session.get(User, uid), session)


@router.get("/bets")
def my_bets(uid: int = Depends(current_user_id), session: Session = Depends(get_session)):
    from ..services.betting_service import _bet_dict
    bets = session.exec(select(Bet).where(Bet.user_id == uid)
                        .order_by(Bet.created_at.desc())).all()
    return [_bet_dict(b) for b in bets]


@router.get("/ledger")
def my_ledger(uid: int = Depends(current_user_id), session: Session = Depends(get_session)):
    rows = session.exec(select(LedgerEntry).where(LedgerEntry.user_id == uid)
                        .order_by(LedgerEntry.ts.desc())).all()
    return [{"ts": r.ts.isoformat(), "kind": r.kind, "amount": r.amount,
             "balance_after": r.balance_after, "memo": r.memo} for r in rows]


@router.get("/badges")
def my_badges(uid: int = Depends(current_user_id), session: Session = Depends(get_session)):
    owned = {a.code: a.unlocked_at for a in
             session.exec(select(Achievement).where(Achievement.user_id == uid)).all()}
    out = []
    for b in gs.badge_catalog():
        out.append({**b, "unlocked": b["code"] in owned,
                    "unlocked_at": owned[b["code"]].isoformat() if b["code"] in owned else None})
    return out


@router.post("/daily-bonus")
def daily_bonus(uid: int = Depends(current_user_id), session: Session = Depends(get_session)):
    user = session.get(User, uid)
    return gs.claim_daily_bonus(session, user, settings.daily_bonus)
