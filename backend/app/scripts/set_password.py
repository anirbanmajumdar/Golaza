"""Set (or reset) a user's password directly — bootstrap utility.

Use this once on the server to give the admin an initial password without
needing email (which isn't configured until the admin logs in and pastes
their Gmail App Password in the panel):

    python -m app.scripts.set_password admin@example.com 'MyTempPass123'

If the password is omitted, a strong random one is generated and printed.
The named user is created (active admin) if it doesn't exist.
"""

from __future__ import annotations

import secrets
import sys

from sqlmodel import Session, select

from ..core.config import settings
from ..core.db import create_db_and_tables, engine
from ..models import LedgerEntry, User
from ..services.auth_service import hash_password


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m app.scripts.set_password <email> [password]")
        raise SystemExit(2)
    email = sys.argv[1].lower().strip()
    password = sys.argv[2] if len(sys.argv) > 2 else secrets.token_urlsafe(9)
    create_db_and_tables()
    with Session(engine) as s:
        user = s.exec(select(User).where(User.email == email)).first()
        if not user:
            user = User(email=email, display_name=email.split("@")[0],
                        balance=settings.starting_balance, is_admin=True, status="active")
            s.add(user); s.commit(); s.refresh(user)
            s.add(LedgerEntry(user_id=user.id, kind="signup",
                              amount=settings.starting_balance,
                              balance_after=user.balance, memo="bootstrap"))
        user.password_hash = hash_password(password)
        user.status = "active"
        user.is_admin = True
        s.add(user); s.commit()
    print(f"OK — {email} can now log in.")
    if len(sys.argv) <= 2:
        print(f"Temporary password: {password}")
        print("Log in, then change it from the panel / Forgot-password.")


if __name__ == "__main__":
    main()
