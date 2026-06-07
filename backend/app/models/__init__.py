"""Importing this package registers every table on SQLModel.metadata."""

from .betting import Bet, LedgerEntry
from .catalog import Match, Team
from .social import Achievement, League, LeagueMember, Setting
from .user import OtpCode, User

__all__ = [
    "User", "OtpCode", "Team", "Match", "Bet", "LedgerEntry",
    "Achievement", "League", "LeagueMember", "Setting",
]
