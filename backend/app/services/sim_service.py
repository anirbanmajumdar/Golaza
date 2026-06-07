"""Runs and caches the Monte-Carlo tournament simulation. Keyed on a hash
of the current Elo vector so it auto-invalidates whenever ratings move
(e.g. after results are entered)."""

from __future__ import annotations

import hashlib
import logging

from sqlmodel import Session, select

from ..core.config import settings
from ..models import Team
from ..quant.odds import fair_odds, quote_odds
from ..quant.simulate import simulate_tournament

log = logging.getLogger("golazo.sim")

_cache: dict[str, dict] = {}


def _signature(teams: list[dict], n: int) -> str:
    raw = ";".join(f"{t['code']}:{round(t['elo'])}" for t in sorted(teams, key=lambda x: x["code"]))
    return hashlib.sha256(f"{n}|{raw}".encode()).hexdigest()[:16]


def _teams_payload(session: Session) -> list[dict]:
    return [
        {"code": t.code, "name": t.name, "group": t.group, "flag": t.flag,
         "elo": t.elo, "is_host": t.is_host}
        for t in session.exec(select(Team)).all()
    ]


def get_simulation(session: Session, n: int | None = None, force: bool = False) -> dict:
    n = n or settings.sim_default_n
    teams = _teams_payload(session)
    if len(teams) < 48:
        return {"ready": False, "reason": "teams not seeded yet"}
    sig = _signature(teams, n)
    if not force and sig in _cache:
        return _cache[sig]

    log.info("running tournament simulation (n=%d, sig=%s)", n, sig)
    raw = simulate_tournament(teams, n_sims=n)
    name = {t["code"]: t["name"] for t in teams}
    flag = {t["code"]: t["flag"] for t in teams}
    group = {t["code"]: t["group"] for t in teams}

    rows = []
    for code, r in raw["teams"].items():
        p = r["p_champion"]
        rows.append({
            **r,
            "name": name[code], "flag": flag[code], "group": group[code],
            "champion_fair_odds": round(fair_odds(p), 1) if p > 0 else None,
            "champion_odds": quote_odds({"win": p}, settings.house_overround)["win"] if p > 0 else None,
        })
    rows.sort(key=lambda x: x["p_champion"], reverse=True)
    result = {"ready": True, "n_sims": raw["n_sims"], "signature": sig, "teams": rows}
    _cache[sig] = result
    return result


def invalidate() -> None:
    _cache.clear()
