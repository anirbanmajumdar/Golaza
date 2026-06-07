"""Runtime app settings stored in the DB (admin panel), overriding env
defaults. Currently: SMTP / Gmail config so the admin can paste their
Gmail App Password in the UI instead of editing .env on the server."""

from __future__ import annotations

from sqlmodel import Session, select

from ..core.config import settings as cfg
from ..core.db import engine
from ..models import Setting

_SMTP_FIELDS = ("smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from")


def _all() -> dict[str, str]:
    with Session(engine) as s:
        return {r.key: r.value for r in s.exec(select(Setting)).all() if r.value is not None}


def get_smtp() -> dict:
    """Effective SMTP config: DB value if set, else env default."""
    db = _all()
    return {
        "host": db.get("smtp_host") or cfg.smtp_host,
        "port": int(db.get("smtp_port") or cfg.smtp_port),
        "user": db.get("smtp_user") or cfg.smtp_user,
        "password": db.get("smtp_password") or cfg.smtp_password,
        "from_addr": db.get("smtp_from") or cfg.smtp_from,
        "tls": cfg.smtp_tls,
    }


def get_smtp_public() -> dict:
    """SMTP config for the admin UI — never returns the password itself."""
    db = _all()
    eff = get_smtp()
    source = "db" if db.get("smtp_host") else ("env" if cfg.smtp_host else "none")
    return {
        "smtp_host": eff["host"], "smtp_port": eff["port"],
        "smtp_user": eff["user"], "smtp_from": eff["from_addr"],
        "password_set": bool(eff["password"]),
        "configured": bool(eff["host"] and eff["password"]),
        "source": source,
    }


def set_smtp(data: dict) -> dict:
    with Session(engine) as s:
        for k in ("smtp_host", "smtp_port", "smtp_user", "smtp_from"):
            v = data.get(k)
            if v is not None and str(v) != "":
                _upsert(s, k, str(v))
        # only overwrite the password when a non-blank one is supplied
        if data.get("smtp_password"):
            _upsert(s, "smtp_password", str(data["smtp_password"]))
        s.commit()
    return get_smtp_public()


def _upsert(s: Session, key: str, value: str) -> None:
    row = s.get(Setting, key)
    if row:
        row.value = value
    else:
        row = Setting(key=key, value=value)
    s.add(row)
