from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..core.db import get_session
from ..data.players_2026 import stars_for
from ..models import Match, Team
from ..services import sim_service

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
def list_teams(session: Session = Depends(get_session)):
    teams = session.exec(select(Team).order_by(Team.group, Team.elo.desc())).all()
    sim = sim_service.get_simulation(session)
    sim_map = {t["code"]: t for t in sim.get("teams", [])} if sim.get("ready") else {}
    out = []
    for t in teams:
        s = sim_map.get(t.code, {})
        out.append({
            "code": t.code, "name": t.name, "group": t.group,
            "confederation": t.confederation, "flag": t.flag,
            "elo": round(t.elo), "elo_seed": round(t.elo_seed), "fifa_pts": t.fifa_pts,
            "is_host": t.is_host,
            "p_advance": s.get("p_advance"), "p_champion": s.get("p_champion"),
            "champion_odds": s.get("champion_odds"),
        })
    return out


@router.get("/{code}")
def team_detail(code: str, session: Session = Depends(get_session)):
    t = session.exec(select(Team).where(Team.code == code.upper())).first()
    if not t:
        raise HTTPException(404, "team not found")
    sim = sim_service.get_simulation(session)
    s = next((x for x in sim.get("teams", []) if x["code"] == t.code), {}) if sim.get("ready") else {}
    matches = session.exec(
        select(Match).where((Match.home_code == t.code) | (Match.away_code == t.code))
        .order_by(Match.kickoff)).all()
    groupmates = session.exec(
        select(Team).where(Team.group == t.group).order_by(Team.elo.desc())).all()
    return {
        "code": t.code, "name": t.name, "group": t.group,
        "confederation": t.confederation, "flag": t.flag,
        "elo": round(t.elo), "elo_seed": round(t.elo_seed), "fifa_pts": t.fifa_pts,
        "is_host": t.is_host,
        "players": stars_for(t.code),
        "simulation": s,
        "group_table": [{"code": g.code, "name": g.name, "flag": g.flag, "elo": round(g.elo)}
                        for g in groupmates],
        "fixtures": [{"id": m.id, "ext_id": m.ext_id, "stage": m.stage,
                      "home_code": m.home_code, "away_code": m.away_code,
                      "kickoff": m.kickoff.isoformat(), "venue": m.venue,
                      "status": m.status,
                      "score": (f"{m.home_goals}-{m.away_goals}"
                                if m.status == "finished" else None)}
                     for m in matches],
    }
