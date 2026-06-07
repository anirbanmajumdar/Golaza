"""The real 104-match calendar of WC 2026.

72 group matches are the official fixtures (teams, date, venue) from the
draw. The 32 knockout matches are created as dated placeholders (Round
of 32 → Final); their participants are filled in as the group stage
resolves, and the Monte-Carlo simulator builds the full bracket itself.

Match `kickoff` is a timezone-aware UTC datetime; we stagger the day's
games across a few hours purely for display ordering.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# (day-in-June, home, away, group, venue)
_GROUP: list[tuple] = [
    (11, "MEX", "RSA", "A", "Mexico City"),
    (11, "KOR", "CZE", "A", "Guadalajara (Zapopan)"),
    (12, "CAN", "BIH", "B", "Toronto"),
    (12, "USA", "PAR", "D", "Los Angeles (Inglewood)"),
    (13, "QAT", "SUI", "B", "San Francisco Bay (Santa Clara)"),
    (13, "BRA", "MAR", "C", "New York/NJ (East Rutherford)"),
    (13, "HAI", "SCO", "C", "Boston (Foxborough)"),
    (13, "AUS", "TUR", "D", "Vancouver"),
    (14, "GER", "CUW", "E", "Houston"),
    (14, "NED", "JPN", "F", "Dallas (Arlington)"),
    (14, "CIV", "ECU", "E", "Philadelphia"),
    (14, "SWE", "TUN", "F", "Monterrey (Guadalupe)"),
    (15, "ESP", "CPV", "H", "Atlanta"),
    (15, "BEL", "EGY", "G", "Seattle"),
    (15, "KSA", "URU", "H", "Miami (Miami Gardens)"),
    (15, "IRN", "NZL", "G", "Los Angeles (Inglewood)"),
    (16, "FRA", "SEN", "I", "New York/NJ (East Rutherford)"),
    (16, "IRQ", "NOR", "I", "Boston (Foxborough)"),
    (16, "ARG", "ALG", "J", "Kansas City"),
    (16, "AUT", "JOR", "J", "San Francisco Bay (Santa Clara)"),
    (17, "POR", "COD", "K", "Houston"),
    (17, "ENG", "CRO", "L", "Dallas (Arlington)"),
    (17, "GHA", "PAN", "L", "Toronto"),
    (17, "UZB", "COL", "K", "Mexico City"),
    (18, "CZE", "RSA", "A", "Atlanta"),
    (18, "SUI", "BIH", "B", "Los Angeles (Inglewood)"),
    (18, "CAN", "QAT", "B", "Vancouver"),
    (18, "MEX", "KOR", "A", "Guadalajara (Zapopan)"),
    (19, "USA", "AUS", "D", "Seattle"),
    (19, "SCO", "MAR", "C", "Boston (Foxborough)"),
    (19, "BRA", "HAI", "C", "Philadelphia"),
    (19, "TUR", "PAR", "D", "San Francisco Bay (Santa Clara)"),
    (20, "NED", "SWE", "F", "Houston"),
    (20, "GER", "CIV", "E", "Toronto"),
    (20, "ECU", "CUW", "E", "Kansas City"),
    (20, "TUN", "JPN", "F", "Monterrey (Guadalupe)"),
    (21, "ESP", "KSA", "H", "Atlanta"),
    (21, "BEL", "IRN", "G", "Los Angeles (Inglewood)"),
    (21, "URU", "CPV", "H", "Miami (Miami Gardens)"),
    (21, "NZL", "EGY", "G", "Vancouver"),
    (22, "ARG", "AUT", "J", "Dallas (Arlington)"),
    (22, "FRA", "IRQ", "I", "Philadelphia"),
    (22, "NOR", "SEN", "I", "New York/NJ (East Rutherford)"),
    (22, "JOR", "ALG", "J", "San Francisco Bay (Santa Clara)"),
    (23, "POR", "UZB", "K", "Houston"),
    (23, "ENG", "GHA", "L", "Boston (Foxborough)"),
    (23, "PAN", "CRO", "L", "Toronto"),
    (23, "COL", "COD", "K", "Guadalajara (Zapopan)"),
    (24, "SUI", "CAN", "B", "Vancouver"),
    (24, "BIH", "QAT", "B", "Seattle"),
    (24, "SCO", "BRA", "C", "Miami (Miami Gardens)"),
    (24, "MAR", "HAI", "C", "Atlanta"),
    (24, "CZE", "MEX", "A", "Mexico City"),
    (24, "RSA", "KOR", "A", "Monterrey (Guadalupe)"),
    (25, "ECU", "GER", "E", "New York/NJ (East Rutherford)"),
    (25, "CUW", "CIV", "E", "Philadelphia"),
    (25, "JPN", "SWE", "F", "Dallas (Arlington)"),
    (25, "TUN", "NED", "F", "Kansas City"),
    (25, "TUR", "USA", "D", "Los Angeles (Inglewood)"),
    (25, "PAR", "AUS", "D", "San Francisco Bay (Santa Clara)"),
    (26, "NOR", "FRA", "I", "Boston (Foxborough)"),
    (26, "SEN", "IRQ", "I", "Toronto"),
    (26, "CPV", "KSA", "H", "Houston"),
    (26, "URU", "ESP", "H", "Guadalajara (Zapopan)"),
    (26, "EGY", "IRN", "G", "Seattle"),
    (26, "NZL", "BEL", "G", "Vancouver"),
    (27, "PAN", "ENG", "L", "New York/NJ (East Rutherford)"),
    (27, "CRO", "GHA", "L", "Philadelphia"),
    (27, "COL", "POR", "K", "Miami (Miami Gardens)"),
    (27, "COD", "UZB", "K", "Atlanta"),
    (27, "ALG", "AUT", "J", "Kansas City"),
    (27, "JOR", "ARG", "J", "Dallas (Arlington)"),
]

# Knockout stage: (stage_code, label, count, first_day, month)
_KNOCKOUT: list[tuple] = [
    ("R32", "Round of 32",   16, 28, 6),
    ("R16", "Round of 16",    8,  4, 7),
    ("QF",  "Quarter-final",  4,  9, 7),
    ("SF",  "Semi-final",     2, 14, 7),
    ("3RD", "Third place",    1, 18, 7),
    ("FIN", "Final",          1, 19, 7),
]


def _kick(month: int, day: int, slot: int) -> datetime:
    hours = [16, 19, 22, 1, 4, 23]  # staggered display ordering
    base = datetime(2026, month, day, 0, 0, tzinfo=timezone.utc)
    h = hours[slot % len(hours)]
    extra = 1 if h < 12 else 0  # early-hour kickoffs roll to next calendar day
    return base + timedelta(days=extra, hours=h)


def group_matches() -> list[dict]:
    out: list[dict] = []
    slot_for_day: dict[int, int] = {}
    for i, (day, home, away, group, venue) in enumerate(_GROUP, start=1):
        slot = slot_for_day.get(day, 0)
        slot_for_day[day] = slot + 1
        out.append({
            "ext_id": f"G{i:02d}",
            "stage": "group",
            "group": group,
            "home_code": home,
            "away_code": away,
            "venue": venue,
            "kickoff": _kick(6, day, slot),
            "round_order": day,
        })
    return out


def knockout_matches() -> list[dict]:
    out: list[dict] = []
    n = 0
    hours = [16, 19, 22, 13]
    for stage, label, count, first_day, month in _KNOCKOUT:
        base = datetime(2026, month, first_day, 0, 0, tzinfo=timezone.utc)
        for j in range(count):
            n += 1
            kickoff = base + timedelta(days=j // 4, hours=hours[j % len(hours)])
            out.append({
                "ext_id": f"{stage}-{j+1}",
                "stage": stage,
                "stage_label": label,
                "group": None,
                "home_code": None,
                "away_code": None,
                "venue": "Final: New York/NJ" if stage == "FIN" else "TBD",
                "kickoff": kickoff,
                "round_order": 100 + n,
            })
    return out


def all_matches() -> list[dict]:
    return group_matches() + knockout_matches()
