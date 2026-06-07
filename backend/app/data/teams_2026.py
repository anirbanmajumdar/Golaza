"""The 48 teams of the 2026 FIFA World Cup (Canada / Mexico / USA).

Groups are the real Final Draw result (Washington D.C., 5 Dec 2025).
`elo` is a World-Football-Elo-style strength rating (mid-2026 plausible
values) and is the single quantitative input the rest of the engine
derives everything from: expected goals, fair odds, simulation outcomes.
`fifa_pts` is shown for flavour. `host` flags the three home nations,
which receive a home-field advantage in the goal model.

Refresh with `python -m app.scripts.refresh_ratings` (tries live Elo,
falls back to these seeds so the app always boots offline in the cloud).
"""

from __future__ import annotations

# code, name, group, confederation, flag emoji, Elo, FIFA points, host?
_TEAMS: list[tuple] = [
    # Group A
    ("MEX", "Mexico",                 "A", "CONCACAF", "🇲🇽", 1880, 1656, True),
    ("RSA", "South Africa",           "A", "CAF",      "🇿🇦", 1720, 1444, False),
    ("KOR", "South Korea",            "A", "AFC",      "🇰🇷", 1790, 1575, False),
    ("CZE", "Czechia",                "A", "UEFA",     "🇨🇿", 1820, 1490, False),
    # Group B
    ("CAN", "Canada",                 "B", "CONCACAF", "🇨🇦", 1840, 1530, True),
    ("BIH", "Bosnia & Herzegovina",   "B", "UEFA",     "🇧🇦", 1730, 1430, False),
    ("QAT", "Qatar",                  "B", "AFC",      "🇶🇦", 1700, 1410, False),
    ("SUI", "Switzerland",            "B", "UEFA",     "🇨🇭", 1860, 1648, False),
    # Group C
    ("BRA", "Brazil",                 "C", "CONMEBOL", "🇧🇷", 2000, 1856, False),
    ("MAR", "Morocco",                "C", "CAF",      "🇲🇦", 1870, 1700, False),
    ("HAI", "Haiti",                  "C", "CONCACAF", "🇭🇹", 1600, 1240, False),
    ("SCO", "Scotland",               "C", "UEFA",     "🏴󠁧󠁢󠁳󠁣󠁴󠁿", 1800, 1500, False),
    # Group D
    ("USA", "United States",          "D", "CONCACAF", "🇺🇸", 1860, 1660, True),
    ("PAR", "Paraguay",               "D", "CONMEBOL", "🇵🇾", 1760, 1480, False),
    ("AUS", "Australia",              "D", "AFC",      "🇦🇺", 1770, 1500, False),
    ("TUR", "Türkiye",                "D", "UEFA",     "🇹🇷", 1850, 1620, False),
    # Group E
    ("GER", "Germany",                "E", "UEFA",     "🇩🇪", 1930, 1720, False),
    ("CUW", "Curaçao",                "E", "CONCACAF", "🇨🇼", 1620, 1280, False),
    ("CIV", "Ivory Coast",            "E", "CAF",      "🇨🇮", 1800, 1530, False),
    ("ECU", "Ecuador",                "E", "CONMEBOL", "🇪🇨", 1820, 1570, False),
    # Group F
    ("NED", "Netherlands",            "F", "UEFA",     "🇳🇱", 1960, 1750, False),
    ("JPN", "Japan",                  "F", "AFC",      "🇯🇵", 1850, 1640, False),
    ("SWE", "Sweden",                 "F", "UEFA",     "🇸🇪", 1800, 1520, False),
    ("TUN", "Tunisia",                "F", "CAF",      "🇹🇳", 1760, 1470, False),
    # Group G
    ("BEL", "Belgium",                "G", "UEFA",     "🇧🇪", 1930, 1740, False),
    ("EGY", "Egypt",                  "G", "CAF",      "🇪🇬", 1790, 1510, False),
    ("IRN", "Iran",                   "G", "AFC",      "🇮🇷", 1810, 1560, False),
    ("NZL", "New Zealand",            "G", "OFC",      "🇳🇿", 1680, 1320, False),
    # Group H
    ("ESP", "Spain",                  "H", "UEFA",     "🇪🇸", 2050, 1875, False),
    ("CPV", "Cape Verde",             "H", "CAF",      "🇨🇻", 1660, 1340, False),
    ("KSA", "Saudi Arabia",           "H", "AFC",      "🇸🇦", 1700, 1420, False),
    ("URU", "Uruguay",                "H", "CONMEBOL", "🇺🇾", 1900, 1680, False),
    # Group I
    ("FRA", "France",                 "I", "UEFA",     "🇫🇷", 2080, 1860, False),
    ("SEN", "Senegal",                "I", "CAF",      "🇸🇳", 1850, 1630, False),
    ("IRQ", "Iraq",                   "I", "AFC",      "🇮🇶", 1700, 1400, False),
    ("NOR", "Norway",                 "I", "UEFA",     "🇳🇴", 1880, 1590, False),
    # Group J
    ("ARG", "Argentina",              "J", "CONMEBOL", "🇦🇷", 2120, 1890, False),
    ("ALG", "Algeria",                "J", "CAF",      "🇩🇿", 1800, 1530, False),
    ("AUT", "Austria",                "J", "UEFA",     "🇦🇹", 1830, 1580, False),
    ("JOR", "Jordan",                 "J", "AFC",      "🇯🇴", 1680, 1360, False),
    # Group K
    ("POR", "Portugal",               "K", "UEFA",     "🇵🇹", 1970, 1770, False),
    ("COD", "DR Congo",               "K", "CAF",      "🇨🇩", 1760, 1450, False),
    ("UZB", "Uzbekistan",             "K", "AFC",      "🇺🇿", 1730, 1440, False),
    ("COL", "Colombia",               "K", "CONMEBOL", "🇨🇴", 1900, 1700, False),
    # Group L
    ("ENG", "England",                "L", "UEFA",     "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 1980, 1810, False),
    ("CRO", "Croatia",                "L", "UEFA",     "🇭🇷", 1860, 1650, False),
    ("GHA", "Ghana",                  "L", "CAF",      "🇬🇭", 1760, 1460, False),
    ("PAN", "Panama",                 "L", "CONCACAF", "🇵🇦", 1680, 1380, False),
]

GROUPS = list("ABCDEFGHIJKL")  # 12 groups of 4


def all_teams() -> list[dict]:
    return [
        {
            "code": c, "name": n, "group": g, "confederation": conf,
            "flag": flag, "elo": elo, "fifa_pts": fifa, "is_host": host,
        }
        for (c, n, g, conf, flag, elo, fifa, host) in _TEAMS
    ]


def teams_in_group(group: str) -> list[dict]:
    return [t for t in all_teams() if t["group"] == group]


def by_code() -> dict[str, dict]:
    return {t["code"]: t for t in all_teams()}
