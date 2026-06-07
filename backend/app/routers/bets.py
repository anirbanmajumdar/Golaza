from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from ..core.db import get_session
from ..core.security import current_user_id
from ..models import Match, User
from ..quant.odds import expected_value, kelly_fraction
from ..services import betting_service, market_service

router = APIRouter(prefix="/bets", tags=["bets"])


class PlaceBet(BaseModel):
    match_id: int
    market: str = "1X2"
    selection: str
    stake: int
    confidence: int = 60
    probs: dict[str, float] | None = None


class AnalyzeBet(BaseModel):
    match_id: int
    market: str = "1X2"
    selection: str
    confidence: int = 60
    stake: int = 100


@router.post("")
def place(payload: PlaceBet, uid: int = Depends(current_user_id),
          session: Session = Depends(get_session)):
    user = session.get(User, uid)
    match = session.get(Match, payload.match_id)
    if not match:
        raise HTTPException(404, "match not found")
    return betting_service.place_bet(
        session, user, match, payload.market, payload.selection,
        payload.stake, payload.confidence, payload.probs)


@router.post("/analyze")
def analyze(payload: AnalyzeBet, session: Session = Depends(get_session)):
    """Pre-bet decision support: model prob, your implied belief, the
    edge (EV) and the Kelly-optimal stake fraction — no coins spent."""
    match = session.get(Match, payload.match_id)
    if not match:
        raise HTTPException(404, "match not found")
    quotes = market_service.build_markets(session, match)
    odds = market_service.selection_odds(quotes, payload.market, payload.selection)
    model_prob = market_service.selection_prob(quotes, payload.market, payload.selection)
    if odds is None or model_prob is None:
        raise HTTPException(400, "unknown market/selection")
    user_prob, _ = betting_service._belief_vector(
        payload.market, payload.selection, payload.confidence, quotes["model"], None)
    ev = expected_value(user_prob, odds)
    kf = kelly_fraction(user_prob, odds)
    return {
        "odds": odds, "model_prob": round(model_prob, 4),
        "user_prob": round(user_prob, 4),
        "edge_vs_model": round(user_prob - model_prob, 4),
        "expected_value_per_coin": round(ev, 4),
        "expected_value_on_stake": round(ev * payload.stake, 2),
        "kelly_fraction": round(kf, 4),
        "half_kelly_pct": round(kf * 50, 2),
        "verdict": "value bet ✅" if ev > 0 else "negative edge ⚠️",
    }
