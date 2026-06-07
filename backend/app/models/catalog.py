from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str
    group: str = Field(index=True)
    confederation: str
    flag: str
    elo: float            # live rating (updated as results land)
    elo_seed: float       # pre-tournament seed (for reference)
    fifa_pts: int
    is_host: bool = False


class Match(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ext_id: str = Field(index=True, unique=True)
    stage: str = Field(index=True)             # group / R32 / R16 / QF / SF / 3RD / FIN
    stage_label: str | None = None
    group: str | None = Field(default=None, index=True)
    home_code: str | None = None
    away_code: str | None = None
    venue: str = "TBD"
    kickoff: datetime = Field(index=True)
    round_order: int = 0
    status: str = Field(default="scheduled", index=True)  # scheduled/live/finished
    home_goals: int | None = None
    away_goals: int | None = None
    result: str | None = None                  # home / draw / away
