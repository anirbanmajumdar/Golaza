from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Setting(SQLModel, table=True):
    """Generic key/value app settings (e.g. SMTP config set from the admin
    panel). Overrides env defaults at runtime."""
    key: str = Field(primary_key=True)
    value: str | None = None


class Achievement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    code: str                            # badge code, see gamification_service.BADGES
    unlocked_at: datetime = Field(default_factory=_now)


class League(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    join_code: str = Field(index=True, unique=True)
    owner_id: int
    created_at: datetime = Field(default_factory=_now)


class LeagueMember(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    league_id: int = Field(index=True)
    user_id: int = Field(index=True)
    joined_at: datetime = Field(default_factory=_now)
