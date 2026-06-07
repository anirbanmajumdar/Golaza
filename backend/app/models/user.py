from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    display_name: str
    avatar_seed: str = "golazo"
    password_hash: str | None = None          # set on invite-accept / reset
    status: str = Field(default="invited", index=True)  # invited / active / disabled
    invited_by: str | None = None
    balance: int = 10_000
    xp: int = 0
    current_streak: int = 0      # consecutive correct settled bets
    best_streak: int = 0
    last_bonus_at: datetime | None = None
    # forecasting-skill accumulators (proper scoring rules)
    brier_sum: float = 0.0
    brier_ref_sum: float = 0.0   # reference (uniform-prior) Brier over same bets
    brier_count: int = 0
    is_admin: bool = False
    created_at: datetime = Field(default_factory=_now)


class OtpCode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    code_hash: str
    expires_at: datetime
    consumed: bool = False
    attempts: int = 0
    created_at: datetime = Field(default_factory=_now)
