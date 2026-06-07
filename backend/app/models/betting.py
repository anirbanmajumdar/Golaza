from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Bet(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    match_id: int = Field(index=True)
    market: str = "1X2"                 # 1X2 / OU25 / BTTS / OUTRIGHT
    selection: str                       # home/draw/away | over/under | yes/no | <team code>
    stake: int
    odds: float                          # locked decimal odds at placement
    model_prob: float                    # model's fair prob for the selection
    user_prob: float | None = None       # user's stated prob for the selection
    probs_json: str | None = None        # full {home,draw,away} belief vector (1X2)
    confidence: int | None = None        # 50–99 slider
    status: str = Field(default="open", index=True)  # open/won/lost/void
    payout: int = 0
    brier: float | None = None           # forecast Brier once settled (1X2)
    created_at: datetime = Field(default_factory=_now)
    settled_at: datetime | None = None


class LedgerEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    ts: datetime = Field(default_factory=_now)
    kind: str                            # signup/bonus/bet/payout/refund/achievement
    amount: int                          # signed coins
    balance_after: int
    memo: str | None = None
