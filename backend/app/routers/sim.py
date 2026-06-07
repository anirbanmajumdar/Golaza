from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..core.db import get_session
from ..core.security import current_user_id
from ..models import Team, User
from ..quant.odds import fair_odds, quote_odds
from ..quant.poisson import build_model
from ..services import gamification_service as gs
from ..services import market_service, sim_service

router = APIRouter(prefix="/sim", tags=["simulation"])


@router.get("/tournament")
def tournament(n: int | None = Query(None, ge=200, le=50000),
               session: Session = Depends(get_session)):
    return sim_service.get_simulation(session, n)


@router.post("/run")
def run(n: int | None = Query(None, ge=200, le=50000),
        uid: int = Depends(current_user_id), session: Session = Depends(get_session)):
    user = session.get(User, uid)
    gs.award_badge(session, user, "the_quant")
    session.commit()
    return sim_service.get_simulation(session, n, force=True)


@router.get("/h2h")
def head_to_head(home: str, away: str, host: bool = False,
                 session: Session = Depends(get_session)):
    """Simulate any hypothetical matchup from current Elo — the
    Dixon–Coles scoreline distribution + quoted markets."""
    h = session.exec(select(Team).where(Team.code == home.upper())).first()
    a = session.exec(select(Team).where(Team.code == away.upper())).first()
    if not h or not a:
        raise HTTPException(404, "unknown team code")
    ha = market_service.home_advantage(h, a)
    if host:
        from ..quant.elo import HOST_HOME_ADV
        ha = HOST_HOME_ADV
    model = build_model(h.elo, a.elo, ha).as_dict()
    probs = {"home": model["p_home"], "draw": model["p_draw"], "away": model["p_away"]}
    return {
        "home": {"code": h.code, "name": h.name, "flag": h.flag, "elo": round(h.elo)},
        "away": {"code": a.code, "name": a.name, "flag": a.flag, "elo": round(a.elo)},
        "home_advantage": ha,
        "model": model,
        "fair_odds": {k: round(fair_odds(v), 2) for k, v in probs.items()},
        "odds": quote_odds(probs),
    }
