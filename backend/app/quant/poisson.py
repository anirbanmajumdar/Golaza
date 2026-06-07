"""Dixon–Coles bivariate-Poisson match model.

We map an Elo difference to a goal *supremacy* and split a base
expected-total into the two teams' scoring rates λ_home, λ_away:

    supremacy = (R_home − R_away + H) / ELO_PER_GOAL
    λ_home = (BASE_TOTAL + supremacy) / 2
    λ_away = (BASE_TOTAL − supremacy) / 2          (floored at 0.15)

Goals are ~ Poisson(λ). The independence assumption mis-prices low
scores (too few 0-0/1-1), so Dixon & Coles (1997) multiply the joint
pmf by a correction τ on the {0,1}×{0,1} cells governed by ρ < 0:

    P(x, y) = τ_ρ(x, y) · Poisson(x; λ_h) · Poisson(y; λ_a)

The normalised score matrix yields every market we quote: 1X2, exact
score, over/under, both-teams-to-score, and the expected scoreline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

ELO_PER_GOAL = 250.0   # ~400 Elo ≈ 1.6-goal supremacy
BASE_TOTAL = 2.65      # mean total goals in a WC match
RHO = -0.06            # Dixon–Coles low-score correction
MAX_GOALS = 10


def lambdas(elo_home: float, elo_away: float, home_adv: float = 0.0) -> tuple[float, float]:
    supremacy = (elo_home - elo_away + home_adv) / ELO_PER_GOAL
    lam_h = max(0.15, (BASE_TOTAL + supremacy) / 2.0)
    lam_a = max(0.15, (BASE_TOTAL - supremacy) / 2.0)
    return lam_h, lam_a


def _tau(x: int, y: int, lh: float, la: float, rho: float) -> float:
    if x == 0 and y == 0:
        return 1.0 - lh * la * rho
    if x == 0 and y == 1:
        return 1.0 + lh * rho
    if x == 1 and y == 0:
        return 1.0 + la * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(lam_h: float, lam_a: float, rho: float = RHO,
                 max_goals: int = MAX_GOALS) -> np.ndarray:
    h = np.array([math.exp(-lam_h) * lam_h ** i / math.factorial(i)
                  for i in range(max_goals + 1)])
    a = np.array([math.exp(-lam_a) * lam_a ** j / math.factorial(j)
                  for j in range(max_goals + 1)])
    m = np.outer(h, a)
    for x in (0, 1):
        for y in (0, 1):
            m[x, y] *= _tau(x, y, lam_h, lam_a, rho)
    return m / m.sum()


@dataclass
class MatchModel:
    elo_home: float
    elo_away: float
    home_adv: float = 0.0
    lam_home: float = 0.0
    lam_away: float = 0.0
    p_home: float = 0.0
    p_draw: float = 0.0
    p_away: float = 0.0
    exp_goals_home: float = 0.0
    exp_goals_away: float = 0.0
    p_over_2_5: float = 0.0
    p_btts: float = 0.0
    top_scores: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "lambda_home": round(self.lam_home, 3),
            "lambda_away": round(self.lam_away, 3),
            "p_home": self.p_home,
            "p_draw": self.p_draw,
            "p_away": self.p_away,
            "exp_goals_home": round(self.exp_goals_home, 2),
            "exp_goals_away": round(self.exp_goals_away, 2),
            "p_over_2_5": self.p_over_2_5,
            "p_btts": self.p_btts,
            "top_scores": self.top_scores,
        }


def build_model(elo_home: float, elo_away: float, home_adv: float = 0.0) -> MatchModel:
    lh, la = lambdas(elo_home, elo_away, home_adv)
    m = score_matrix(lh, la)
    n = m.shape[0]
    idx = np.arange(n)
    p_home = float(np.tril(m, -1).sum())   # home goals > away goals
    p_away = float(np.triu(m, 1).sum())
    p_draw = float(np.trace(m))
    total = idx[:, None] + idx[None, :]
    p_over = float(m[total >= 3].sum())
    btts = float(m[1:, 1:].sum())
    eg_h = float((idx[:, None] * m).sum())
    eg_a = float((idx[None, :] * m).sum())
    # most-likely exact scores
    flat = [(int(i), int(j), float(m[i, j])) for i in range(n) for j in range(n)]
    flat.sort(key=lambda t: t[2], reverse=True)
    top = [{"score": f"{i}-{j}", "prob": round(p, 4)} for (i, j, p) in flat[:5]]
    return MatchModel(
        elo_home=elo_home, elo_away=elo_away, home_adv=home_adv,
        lam_home=lh, lam_away=la,
        p_home=round(p_home, 4), p_draw=round(p_draw, 4), p_away=round(p_away, 4),
        exp_goals_home=eg_h, exp_goals_away=eg_a,
        p_over_2_5=round(p_over, 4), p_btts=round(btts, 4), top_scores=top,
    )
