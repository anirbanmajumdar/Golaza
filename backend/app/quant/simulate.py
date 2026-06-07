"""Monte-Carlo simulation of the whole tournament.

Each replication plays all 72 group matches (goals ~ independent Poisson
with the Dixon–Coles λ's), ranks every group by FIFA tiebreakers
(points → goal difference → goals for → draw), promotes the 12 group
winners, 12 runners-up and the 8 best third-placed teams, then plays a
32-team single-elimination bracket (penalty shoot-outs resolved by an
Elo-weighted Bernoulli). Aggregating N replications gives each nation's
probability of winning its group, advancing, reaching each round and
lifting the trophy — a full predictive distribution over the event.

Host nations carry an Elo bump (home advantage) in every match.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from .elo import HOST_HOME_ADV
from .poisson import lambdas


def _effective_elo(teams: list[dict]) -> dict[str, float]:
    return {t["code"]: t["elo"] + (HOST_HOME_ADV if t.get("is_host") else 0.0)
            for t in teams}


def _play(rng, eff: dict, a: str, b: str) -> tuple[int, int]:
    lh, la = lambdas(eff[a], eff[b])
    return int(rng.poisson(lh)), int(rng.poisson(la))


def _ko_winner(rng, eff: dict, a: str, b: str) -> str:
    ga, gb = _play(rng, eff, a, b)
    if ga > gb:
        return a
    if gb > ga:
        return b
    p_a = 0.5 + (eff[a] - eff[b]) / 4000.0  # penalties: slight edge to stronger
    p_a = min(0.95, max(0.05, p_a))
    return a if rng.random() < p_a else b


def simulate_tournament(teams: list[dict], n_sims: int = 2000,
                        seed: int | None = 2026) -> dict:
    rng = np.random.default_rng(seed)
    eff = _effective_elo(teams)
    groups: dict[str, list[str]] = defaultdict(list)
    for t in teams:
        groups[t["group"]].append(t["code"])
    group_letters = sorted(groups)

    C = {k: defaultdict(float) for k in
         ("champion", "final", "semi", "quarter", "r16", "advance",
          "group_winner", "group_runner", "points")}

    for _ in range(n_sims):
        thirds: list[tuple] = []          # (points, gd, gf, code)
        qualifiers: list[str] = []
        for g in group_letters:
            codes = groups[g]
            pts = {c: 0 for c in codes}
            gf = {c: 0 for c in codes}
            ga = {c: 0 for c in codes}
            for i in range(len(codes)):
                for j in range(i + 1, len(codes)):
                    a, b = codes[i], codes[j]
                    sa, sb = _play(rng, eff, a, b)
                    gf[a] += sa; ga[a] += sb; gf[b] += sb; ga[b] += sa
                    if sa > sb:
                        pts[a] += 3
                    elif sb > sa:
                        pts[b] += 3
                    else:
                        pts[a] += 1; pts[b] += 1
            ranked = sorted(
                codes,
                key=lambda c: (pts[c], gf[c] - ga[c], gf[c], rng.random()),
                reverse=True,
            )
            for c in codes:
                C["points"][c] += pts[c]
            C["group_winner"][ranked[0]] += 1
            C["group_runner"][ranked[1]] += 1
            qualifiers.extend([ranked[0], ranked[1]])
            t3 = ranked[2]
            thirds.append((pts[t3], gf[t3] - ga[t3], gf[t3], t3))

        thirds.sort(key=lambda x: (x[0], x[1], x[2], rng.random()), reverse=True)
        qualifiers.extend([t[3] for t in thirds[:8]])  # 24 + 8 = 32

        for c in qualifiers:
            C["advance"][c] += 1

        bracket = list(qualifiers)
        rng.shuffle(bracket)
        # 32 → 16 → 8 → 4 → 2 → 1, tagging the round each team reaches.
        for round_key in ("r16", "quarter", "semi", "final", "champion"):
            nxt = [_ko_winner(rng, eff, bracket[i], bracket[i + 1])
                   for i in range(0, len(bracket), 2)]
            for c in nxt:
                C[round_key][c] += 1
            bracket = nxt

    out = {}
    for t in teams:
        c = t["code"]
        out[c] = {
            "code": c,
            "p_group_winner": round(C["group_winner"][c] / n_sims, 4),
            "p_runner_up": round(C["group_runner"][c] / n_sims, 4),
            "p_advance": round(C["advance"][c] / n_sims, 4),
            "p_round_of_16": round(C["r16"][c] / n_sims, 4),
            "p_quarter": round(C["quarter"][c] / n_sims, 4),
            "p_semi": round(C["semi"][c] / n_sims, 4),
            "p_final": round(C["final"][c] / n_sims, 4),
            "p_champion": round(C["champion"][c] / n_sims, 4),
            "exp_group_points": round(C["points"][c] / n_sims, 2),
        }
    return {"n_sims": n_sims, "teams": out}
