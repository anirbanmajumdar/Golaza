"""Place and settle bets. This is where probability theory meets the
ledger: odds are locked from the model at placement, payouts are exact,
Elo ratings update on every result, and 1X2 forecasts are graded with a
proper scoring rule so skill (not just luck) is measurable.

NO real money — `balance` is virtual GOLAZO coins (₲).
"""

from __future__ import annotations

import json
import logging

from fastapi import HTTPException, status
from sqlmodel import Session, select

from ..models import Bet, LedgerEntry, Match, Team, User
from ..quant import elo as elo_mod
from ..quant.odds import expected_value, kelly_fraction
from ..quant.scoring import UNIFORM, brier, normalize
from . import gamification_service as gs
from . import market_service, sim_service

log = logging.getLogger("golazo.bets")


# ── placement ────────────────────────────────────────────────────────────

def _belief_vector(market: str, selection: str, confidence: int,
                   model: dict, probs: dict | None) -> tuple[float, dict | None]:
    """Return (user_prob_for_selection, full_1x2_vector_or_None)."""
    if market == "1X2":
        if probs:
            vec = normalize({k: float(probs.get(k, 0.0)) for k in ("home", "draw", "away")})
        else:
            c = max(0.34, min(0.99, confidence / 100.0))
            others = [k for k in ("home", "draw", "away") if k != selection]
            mtot = sum(model.get(f"p_{o}", 0.0) for o in others)
            rem = 1.0 - c
            if mtot <= 0:
                vec = {selection: c, **{o: rem / 2 for o in others}}
            else:
                vec = {selection: c,
                       **{o: rem * model.get(f"p_{o}", 0.0) / mtot for o in others}}
            vec = normalize(vec)
        return vec[selection], vec
    # binary markets: belief in the chosen side only
    return max(0.34, min(0.99, confidence / 100.0)), None


def place_bet(session: Session, user: User, match: Match, market: str,
              selection: str, stake: int, confidence: int = 60,
              probs: dict | None = None) -> dict:
    if match.status != "scheduled":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "market closed for this match")
    if stake <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "stake must be positive")
    if stake > user.balance:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "insufficient balance")

    quotes = market_service.build_markets(session, match)
    odds = market_service.selection_odds(quotes, market, selection)
    model_prob = market_service.selection_prob(quotes, market, selection)
    if odds is None or model_prob is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "unknown market/selection")

    user_prob, vec = _belief_vector(market, selection, confidence, quotes["model"], probs)

    # economy
    user.balance -= stake
    bet = Bet(user_id=user.id, match_id=match.id, market=market, selection=selection,
              stake=stake, odds=odds, model_prob=model_prob, user_prob=user_prob,
              probs_json=json.dumps(vec) if vec else None, confidence=confidence)
    session.add(bet)
    session.add(LedgerEntry(user_id=user.id, kind="bet", amount=-stake,
                            balance_after=user.balance, memo=f"{market}:{selection} @ {odds}"))
    gs.grant_xp(user, 10)

    # badges
    gs.award_badge(session, user, "first_kick")
    if stake >= 2000:
        gs.award_badge(session, user, "high_roller")
    if expected_value(user_prob, odds) > 0:
        gs.award_badge(session, user, "sharp_shooter")
    _check_volume_badges(session, user)

    session.add(user)
    session.commit()
    session.refresh(bet)
    return {
        "bet": _bet_dict(bet),
        "expected_value": round(expected_value(user_prob, odds), 4),
        "kelly_fraction": round(kelly_fraction(user_prob, odds), 4),
        "kelly_stake_suggestion": int(kelly_fraction(user_prob, odds) * (user.balance + stake) * 0.5),
        "balance": user.balance,
    }


def _check_volume_badges(session: Session, user: User) -> None:
    bets = session.exec(select(Bet).where(Bet.user_id == user.id)).all()
    if len(bets) >= 25:
        gs.award_badge(session, user, "regular")
    match_ids = [b.match_id for b in bets]
    if match_ids:
        groups = {m.group for m in session.exec(
            select(Match).where(Match.id.in_(match_ids))).all() if m.group}
        if len(groups) >= 6:
            gs.award_badge(session, user, "globe_trotter")


# ── settlement ───────────────────────────────────────────────────────────

def _outcome(market: str, hg: int, ag: int) -> dict[str, bool]:
    res = "home" if hg > ag else "away" if ag > hg else "draw"
    total = hg + ag
    return {
        "1X2": res,
        "OU25": "over" if total >= 3 else "under",
        "BTTS": "yes" if (hg > 0 and ag > 0) else "no",
    }


def settle_match(session: Session, match: Match, home_goals: int, away_goals: int) -> dict:
    if match.status == "finished":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "match already settled")
    res = "home" if home_goals > away_goals else "away" if away_goals > home_goals else "draw"
    match.home_goals, match.away_goals = home_goals, away_goals
    match.result, match.status = res, "finished"
    session.add(match)

    # Elo update
    home = session.exec(select(Team).where(Team.code == match.home_code)).first()
    away = session.exec(select(Team).where(Team.code == match.away_code)).first()
    if home and away:
        ha = market_service.home_advantage(home, away)
        k = elo_mod.K_WORLD_CUP_GROUP if match.stage == "group" else elo_mod.K_WORLD_CUP_KO
        home.elo, away.elo = elo_mod.update(home.elo, away.elo, home_goals, away_goals,
                                            k=k, home_adv=ha)
        session.add(home); session.add(away)

    winners = _outcome("", home_goals, away_goals)
    settled = 0
    for bet in session.exec(select(Bet).where(Bet.match_id == match.id,
                                              Bet.status == "open")).all():
        user = session.get(User, bet.user_id)
        won = winners.get(bet.market) == bet.selection
        if won:
            bet.payout = round(bet.stake * bet.odds)
            bet.status = "won"
            user.balance += bet.payout
            session.add(LedgerEntry(user_id=user.id, kind="payout", amount=bet.payout,
                                    balance_after=user.balance, memo=f"won bet #{bet.id}"))
            user.current_streak += 1
            user.best_streak = max(user.best_streak, user.current_streak)
            gs.grant_xp(user, 25)
            if user.current_streak >= 3:
                gs.award_badge(session, user, "hot_streak_3")
            if user.current_streak >= 5:
                gs.award_badge(session, user, "hot_streak_5")
            if bet.market == "1X2" and bet.model_prob < 0.30:
                gs.award_badge(session, user, "giant_killer")
        else:
            bet.status = "lost"
            user.current_streak = 0

        # forecast skill (1X2 only, proper scoring)
        if bet.market == "1X2" and bet.probs_json:
            vec = json.loads(bet.probs_json)
            b = brier(vec, res)
            bet.brier = round(b, 4)
            user.brier_sum += b
            user.brier_ref_sum += brier(UNIFORM, res)
            user.brier_count += 1
            if user.brier_count >= 10 and user.brier_sum < user.brier_ref_sum:
                gs.award_badge(session, user, "oracle")

        from datetime import datetime, timezone
        bet.settled_at = datetime.now(timezone.utc)
        session.add(bet); session.add(user)
        settled += 1

    session.commit()
    sim_service.invalidate()  # ratings moved → recompute simulation on next call
    return {"match_id": match.id, "result": res, "score": f"{home_goals}-{away_goals}",
            "bets_settled": settled}


# ── serialization ────────────────────────────────────────────────────────

def _bet_dict(bet: Bet) -> dict:
    return {
        "id": bet.id, "match_id": bet.match_id, "market": bet.market,
        "selection": bet.selection, "stake": bet.stake, "odds": bet.odds,
        "model_prob": bet.model_prob, "user_prob": bet.user_prob,
        "confidence": bet.confidence, "status": bet.status, "payout": bet.payout,
        "brier": bet.brier,
        "created_at": bet.created_at.isoformat() if bet.created_at else None,
    }
