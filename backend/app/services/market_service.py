"""Turn a fixture into quotable betting markets using the live Elo +
Dixon–Coles model. Every selection carries the model's fair probability,
fair odds, and the vig-loaded odds we actually book bets at."""

from __future__ import annotations

from sqlmodel import Session, select

from ..core.config import settings
from ..models import Match, Team
from ..quant.elo import HOST_HOME_ADV
from ..quant.odds import fair_odds, quote_odds
from ..quant.poisson import build_model


def _elo_map(session: Session) -> dict[str, Team]:
    return {t.code: t for t in session.exec(select(Team)).all()}


def home_advantage(home: Team, away: Team) -> float:
    if home.is_host:
        return HOST_HOME_ADV
    if away.is_host:
        return -HOST_HOME_ADV
    return 0.0


def _market(name: str, label: str, probs: dict[str, float],
            labels: dict[str, str]) -> dict:
    odds = quote_odds(probs, settings.house_overround)
    return {
        "market": name,
        "label": label,
        "selections": [
            {
                "key": k,
                "label": labels[k],
                "prob": round(probs[k], 4),
                "fair_odds": round(fair_odds(probs[k]), 2),
                "odds": odds[k],
            }
            for k in probs
        ],
    }


def build_markets(session: Session, match: Match) -> dict:
    """Full model + market quotes for a match. Returns {} if teams unknown."""
    teams = _elo_map(session)
    home = teams.get(match.home_code or "")
    away = teams.get(match.away_code or "")
    if not home or not away:
        return {"available": False, "reason": "participants not yet decided"}

    ha = home_advantage(home, away)
    model = build_model(home.elo, away.elo, ha)
    md = model.as_dict()

    markets = [
        _market("1X2", "Match result",
                {"home": md["p_home"], "draw": md["p_draw"], "away": md["p_away"]},
                {"home": home.name, "draw": "Draw", "away": away.name}),
        _market("OU25", "Total goals O/U 2.5",
                {"over": md["p_over_2_5"], "under": round(1 - md["p_over_2_5"], 4)},
                {"over": "Over 2.5", "under": "Under 2.5"}),
        _market("BTTS", "Both teams to score",
                {"yes": md["p_btts"], "no": round(1 - md["p_btts"], 4)},
                {"yes": "Yes", "no": "No"}),
    ]
    return {
        "available": match.status == "scheduled",
        "match_id": match.id,
        "home": {"code": home.code, "name": home.name, "flag": home.flag, "elo": round(home.elo)},
        "away": {"code": away.code, "name": away.name, "flag": away.flag, "elo": round(away.elo)},
        "home_advantage": ha,
        "model": md,
        "markets": markets,
        "overround": settings.house_overround,
    }


def selection_prob(markets: dict, market: str, selection: str) -> float | None:
    for m in markets.get("markets", []):
        if m["market"] == market:
            for s in m["selections"]:
                if s["key"] == selection:
                    return s["prob"]
    return None


def selection_odds(markets: dict, market: str, selection: str) -> float | None:
    for m in markets.get("markets", []):
        if m["market"] == market:
            for s in m["selections"]:
                if s["key"] == selection:
                    return s["odds"]
    return None
