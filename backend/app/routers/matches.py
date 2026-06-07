from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..core.db import get_session
from ..models import Match, Team
from ..services import market_service

router = APIRouter(prefix="/matches", tags=["matches"])


def _team_brief(session: Session, code: str | None) -> dict | None:
    if not code:
        return None
    t = session.exec(select(Team).where(Team.code == code)).first()
    if not t:
        return {"code": code, "name": code, "flag": "🏳️"}
    return {"code": t.code, "name": t.name, "flag": t.flag, "elo": round(t.elo)}


@router.get("")
def list_matches(
    stage: str | None = Query(None),
    group: str | None = Query(None),
    status: str | None = Query(None),
    session: Session = Depends(get_session),
):
    q = select(Match)
    if stage:
        q = q.where(Match.stage == stage)
    if group:
        q = q.where(Match.group == group)
    if status:
        q = q.where(Match.status == status)
    matches = session.exec(q.order_by(Match.kickoff, Match.round_order)).all()
    out = []
    for m in matches:
        quick = None
        if m.home_code and m.away_code and m.status == "scheduled":
            mk = market_service.build_markets(session, m)
            md = mk.get("model", {})
            quick = {"p_home": md.get("p_home"), "p_draw": md.get("p_draw"),
                     "p_away": md.get("p_away")}
        out.append({
            "id": m.id, "ext_id": m.ext_id, "stage": m.stage,
            "stage_label": m.stage_label, "group": m.group,
            "kickoff": m.kickoff.isoformat(), "venue": m.venue, "status": m.status,
            "home": _team_brief(session, m.home_code),
            "away": _team_brief(session, m.away_code),
            "home_goals": m.home_goals, "away_goals": m.away_goals,
            "result": m.result, "model": quick,
        })
    return out


@router.get("/{match_id}")
def match_detail(match_id: int, session: Session = Depends(get_session)):
    m = session.get(Match, match_id)
    if not m:
        raise HTTPException(404, "match not found")
    quotes = market_service.build_markets(session, m)
    return {
        "id": m.id, "ext_id": m.ext_id, "stage": m.stage,
        "stage_label": m.stage_label, "group": m.group,
        "kickoff": m.kickoff.isoformat(), "venue": m.venue, "status": m.status,
        "home_goals": m.home_goals, "away_goals": m.away_goals, "result": m.result,
        "quotes": quotes,
    }
