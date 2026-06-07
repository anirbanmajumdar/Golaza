"""Refresh team Elo from a live source, falling back to the seed values.

Tries the public World-Football-Elo CSV (eloratings.net). On any failure
(offline, schema change, blocked egress) it leaves the seeded ratings in
place so the app keeps working — important for a cloud VM that may have
restricted outbound access.

    python -m app.scripts.refresh_ratings
"""

from __future__ import annotations

import logging

from sqlmodel import Session, select

from ..core.db import engine
from ..models import Team
from ..services import sim_service

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("golazo.refresh")

# eloratings.net uses full country names; map to our codes.
NAME_TO_CODE = {
    "Argentina": "ARG", "France": "FRA", "Spain": "ESP", "Brazil": "BRA",
    "England": "ENG", "Portugal": "POR", "Netherlands": "NED", "Belgium": "BEL",
    "Germany": "GER", "Croatia": "CRO", "Uruguay": "URU", "Colombia": "COL",
    "Morocco": "MAR", "Switzerland": "SUI", "Japan": "JPN", "USA": "USA",
    "Mexico": "MEX", "Senegal": "SEN", "Ecuador": "ECU", "Norway": "NOR",
}


def fetch_live() -> dict[str, float]:
    import csv
    import io
    import urllib.request

    url = "https://www.eloratings.net/World.tsv"
    with urllib.request.urlopen(url, timeout=20) as resp:  # noqa: S310
        text = resp.read().decode("utf-8", "ignore")
    out: dict[str, float] = {}
    for row in csv.reader(io.StringIO(text), delimiter="\t"):
        if len(row) < 3:
            continue
        name, elo = row[1].strip(), row[2].strip()
        code = NAME_TO_CODE.get(name)
        if code:
            try:
                out[code] = float(elo)
            except ValueError:
                pass
    return out


def main() -> None:
    try:
        live = fetch_live()
        log.info("fetched %d live ratings", len(live))
    except Exception as exc:  # noqa: BLE001
        log.warning("live fetch failed (%s); keeping seeds", exc)
        live = {}
    if not live:
        return
    with Session(engine) as session:
        updated = 0
        for t in session.exec(select(Team)).all():
            if t.code in live:
                t.elo = live[t.code]
                session.add(t)
                updated += 1
        session.commit()
        log.info("updated %d team ratings", updated)
    sim_service.invalidate()


if __name__ == "__main__":
    main()
