"""Odds ⇄ probability conversion and bet-sizing theory.

Fair decimal odds are the reciprocal of probability, o = 1/p, so a fair
bet has zero expected value. A book adds an *overround* (vig): we inflate
each implied probability by a factor so Σ 1/o = overround > 1. The house
edge is (overround − 1).

For a punter who believes the true probability is p and is offered odds
o, the per-unit expected value is
    EV = p·(o − 1) − (1 − p)
and the growth-optimal stake fraction is the Kelly criterion
    f* = (p·(o − 1) − (1 − p)) / (o − 1)          (Kelly 1956)
clipped to [0, 1]. We surface EV and a half-Kelly suggestion on every
market so the league rewards genuine edge, not just gambling.
"""

from __future__ import annotations

DEFAULT_OVERROUND = 1.05  # 5% house edge on quoted odds


def fair_odds(p: float) -> float:
    return float("inf") if p <= 0 else 1.0 / p


def quote_odds(probs: dict[str, float], overround: float = DEFAULT_OVERROUND) -> dict[str, float]:
    """Turn fair probabilities into quotable decimal odds with vig."""
    return {k: round(1.0 / (max(p, 1e-9) * overround), 2) for k, p in probs.items()}


def implied_prob(odds: float) -> float:
    return 0.0 if odds <= 0 else 1.0 / odds


def remove_vig(odds: dict[str, float]) -> dict[str, float]:
    """Normalise quoted odds back to a proper probability distribution."""
    raw = {k: implied_prob(o) for k, o in odds.items()}
    s = sum(raw.values()) or 1.0
    return {k: v / s for k, v in raw.items()}


def expected_value(p: float, odds: float, stake: float = 1.0) -> float:
    return stake * (p * (odds - 1.0) - (1.0 - p))


def kelly_fraction(p: float, odds: float) -> float:
    b = odds - 1.0
    if b <= 0:
        return 0.0
    f = (p * b - (1.0 - p)) / b
    return max(0.0, min(1.0, f))


def decimal_to_american(odds: float) -> int:
    if odds >= 2.0:
        return round((odds - 1.0) * 100)
    return round(-100.0 / (odds - 1.0))
