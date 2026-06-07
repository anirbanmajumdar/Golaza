"""World-Football Elo ratings.

The expected (win) score of A vs B is the logistic
    E_A = 1 / (1 + 10^(-(R_A - R_B + H) / 400))
where H is home-field advantage in Elo points. After a result, ratings
update by
    R'_A = R_A + K · G · (W_A − E_A)
with K the match-importance weight, G a goal-difference multiplier
(Hirst/eloratings.net convention), and W_A ∈ {1, 0.5, 0} the result.

This is the canonical paired-comparison model (Elo 1978; Hvattum &
Arntzen 2010 show it is competitive with bookmaker odds for football).
"""

from __future__ import annotations

# Home advantage in Elo points (≈ 0.4 goals). Applied only to host nations
# playing on home soil; knockout/neutral games use 0.
HOST_HOME_ADV = 70.0

# K-factor by match importance (eloratings.net scale).
K_WORLD_CUP_GROUP = 50.0
K_WORLD_CUP_KO = 60.0


def expected_score(r_a: float, r_b: float, home_adv: float = 0.0) -> float:
    """P(A wins) + 0.5·P(draw) — the Elo win-expectancy of A."""
    return 1.0 / (1.0 + 10 ** (-(r_a - r_b + home_adv) / 400.0))


def goal_diff_multiplier(goal_diff: int) -> float:
    """eloratings.net G: dampens blowouts, rewards margin sub-linearly."""
    n = abs(goal_diff)
    if n <= 1:
        return 1.0
    if n == 2:
        return 1.5
    return (11.0 + n) / 8.0


def update(r_a: float, r_b: float, goals_a: int, goals_b: int,
           k: float = K_WORLD_CUP_GROUP, home_adv: float = 0.0) -> tuple[float, float]:
    """Return new (R_A, R_B) after a result. Zero-sum exchange."""
    if goals_a > goals_b:
        w_a = 1.0
    elif goals_a < goals_b:
        w_a = 0.0
    else:
        w_a = 0.5
    e_a = expected_score(r_a, r_b, home_adv)
    g = goal_diff_multiplier(goals_a - goals_b)
    delta = k * g * (w_a - e_a)
    return r_a + delta, r_b - delta
