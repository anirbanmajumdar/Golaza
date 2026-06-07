"""Proper scoring rules for forecast quality.

When a user commits to a probability vector over {home, draw, away} we
grade it with strictly proper scoring rules — ones whose expected score
is optimised only by reporting one's true beliefs:

    Brier score  = Σ_k (p_k − o_k)²            ∈ [0, 2]   (lower better)
    Log loss     = −Σ_k o_k · ln(p_k)                     (lower better)

where o_k is the one-hot outcome. We convert Brier to a Brier *Skill
Score* against a reference forecast (the model, or the climatological
1/3-1/3-1/3 prior):

    BSS = 1 − Brier_user / Brier_ref           (>0 beats the reference)

Averaged over a user's settled predictions this is a calibration-aware
measure of skill that is independent of how many coins they wagered.
"""

from __future__ import annotations

import math

OUTCOMES = ("home", "draw", "away")
UNIFORM = {"home": 1 / 3, "draw": 1 / 3, "away": 1 / 3}


def _onehot(outcome: str) -> dict[str, float]:
    return {k: (1.0 if k == outcome else 0.0) for k in OUTCOMES}


def brier(probs: dict[str, float], outcome: str) -> float:
    o = _onehot(outcome)
    return sum((probs.get(k, 0.0) - o[k]) ** 2 for k in OUTCOMES)


def log_loss(probs: dict[str, float], outcome: str, eps: float = 1e-12) -> float:
    p = max(eps, min(1.0, probs.get(outcome, 0.0)))
    return -math.log(p)


def brier_skill_score(user_brier: float, ref_brier: float) -> float:
    if ref_brier <= 0:
        return 0.0
    return 1.0 - user_brier / ref_brier


def normalize(probs: dict[str, float]) -> dict[str, float]:
    s = sum(max(0.0, probs.get(k, 0.0)) for k in OUTCOMES) or 1.0
    return {k: max(0.0, probs.get(k, 0.0)) / s for k in OUTCOMES}
