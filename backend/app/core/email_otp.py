"""OTP generation + transactional email (invites, password resets).

Codes are hashed (SHA-256) before storage so a DB leak never reveals live
codes. Delivery is plain SMTP (Gmail-friendly: smtp.gmail.com:587 + an
App Password). With no SMTP host configured we degrade to dev mode — the
code / link is logged and returned by the API so the app is fully usable
on a laptop with no mail server.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import settings

log = logging.getLogger("golazo.mail")


def generate_otp() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(settings.otp_length))


def hash_otp(code: str) -> str:
    return hashlib.sha256(f"{settings.secret_key}:{code}".encode()).hexdigest()


def _shell(title: str, inner: str) -> str:
    return f"""\
<div style="font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;max-width:480px;margin:auto">
  <div style="background:linear-gradient(135deg,#0b6e4f,#0a8f5b);color:#fff;padding:24px;border-radius:16px 16px 0 0">
    <h1 style="margin:0;font-size:22px">⚽ GOLAZO 2026</h1>
    <p style="margin:6px 0 0;opacity:.9">{title}</p>
  </div>
  <div style="border:1px solid #eee;border-top:none;padding:24px;border-radius:0 0 16px 16px;color:#13231d">
    {inner}
  </div>
</div>"""


def _send(to: str, subject: str, text: str, html: str) -> bool:
    """Return True if actually emailed, False in dev mode (no SMTP host).
    Uses the effective SMTP config (admin-panel DB value over env)."""
    from ..services.settings_service import get_smtp  # lazy: avoid import cycle
    eff = get_smtp()
    if not eff["host"]:
        log.warning("DEV MODE — no SMTP. %s → %s\n%s", subject, to, text)
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = eff["from_addr"]
    msg["To"] = to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(eff["host"], eff["port"], timeout=20) as s:
        if eff["tls"]:
            s.starttls()
        if eff["user"]:
            s.login(eff["user"], eff["password"])
        s.sendmail(eff["from_addr"], [to], msg.as_string())
    log.info("emailed '%s' to %s", subject, to)
    return True


def send_test(to: str) -> bool:
    """Send a test email — used by the admin panel to verify SMTP. Raises
    on SMTP failure so the panel can surface the exact error."""
    inner = ("<p>✅ Your GOLAZO 2026 email is working.</p>"
             "<p style='color:#666;font-size:13px'>Invites and password "
             "codes will now be delivered from this address.</p>")
    return _send(to, "GOLAZO 2026 — SMTP test", "GOLAZO 2026 SMTP test — it works.",
                 _shell("SMTP test", inner))


def send_otp(email: str, code: str) -> bool:
    inner = (f"<p>Your one-time code to reset your GOLAZO password:</p>"
             f"<p style='font-size:38px;font-weight:800;letter-spacing:10px;color:#0b6e4f;margin:12px 0'>{code}</p>"
             f"<p style='color:#666;font-size:13px'>Expires in {settings.otp_ttl_minutes} minutes. "
             f"If you didn't request this, ignore this email.</p>")
    return _send(email, "Your GOLAZO 2026 password code",
                 f"Your GOLAZO password reset code is {code} "
                 f"(valid {settings.otp_ttl_minutes} min).",
                 _shell("Password reset", inner))


def send_invite(email: str, display_name: str, link: str, inviter: str) -> bool:
    inner = (f"<p>Hi {display_name},</p>"
             f"<p><b>{inviter}</b> invited you to the GOLAZO 2026 World Cup "
             f"prediction league. Set your password to claim your "
             f"₲{settings.starting_balance:,} of coins and start predicting.</p>"
             f"<p style='margin:22px 0'><a href='{link}' "
             f"style='background:#16c784;color:#04130d;padding:12px 22px;border-radius:10px;"
             f"font-weight:700;text-decoration:none'>Set my password →</a></p>"
             f"<p style='color:#666;font-size:13px'>Or paste this link:<br>{link}<br><br>"
             f"This invite expires in {settings.invite_ttl_hours // 24} days.</p>")
    return _send(email, "You're invited to GOLAZO 2026 ⚽",
                 f"{inviter} invited you to GOLAZO 2026. Set your password: {link}",
                 _shell("You're invited", inner))
