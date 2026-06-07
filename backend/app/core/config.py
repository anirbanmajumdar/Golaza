"""Runtime config. Reads env vars (prefix WCB_) with local-dev defaults
so `uvicorn app.main:app` runs with zero setup. Everything that must
change for a cloud deploy is here."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="WCB_",
                                       case_sensitive=False, extra="ignore")

    # storage — SQLite by default (single-file, deploy-friendly, no extra service)
    db_url: str = "sqlite:///./data/golazo.db"

    # auth / JWT
    secret_key: str = "dev-only-change-me-in-prod"
    access_token_ttl_minutes: int = 60 * 24 * 7   # 7 days
    invite_ttl_hours: int = 24 * 7                 # invite link valid 7 days
    otp_ttl_minutes: int = 10
    otp_length: int = 6

    # private league — only these emails are bootstrapped as admins. Admins
    # invite everyone else; nobody can self-register.
    admin_emails: list[str] = ["admin@example.com"]

    # public URL used to build invite / reset links inside emails
    public_base_url: str = "http://localhost:3030"

    # shorten invite/join links via TinyURL (falls back to the full URL on failure)
    shorten_links: bool = True

    # email (OTP delivery). If SMTP is unset we run in dev mode and the
    # OTP is logged + returned in the API response (never do that in prod).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "GOLAZO 2026 <admin@example.com>"
    smtp_tls: bool = True
    dev_echo_otp: bool = True   # also echoes invite links when SMTP is unset

    # economy (virtual coins — NO real money)
    starting_balance: int = 10_000
    daily_bonus: int = 500
    house_overround: float = 1.05

    # simulation
    sim_default_n: int = 2000

    # CORS
    cors_origins: list[str] = ["http://localhost:3030", "http://127.0.0.1:3030"]


settings = Settings()
