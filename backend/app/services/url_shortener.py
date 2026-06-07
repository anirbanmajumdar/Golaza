"""Shorten URLs via TinyURL's keyless create endpoint. Pure stdlib; on any
failure (offline, rate-limited, timeout) it returns the original URL so
invite/join flows never break."""

from __future__ import annotations

import logging
import urllib.parse
import urllib.request

from ..core.config import settings

log = logging.getLogger("golazo.shorten")

_ENDPOINT = "https://tinyurl.com/api-create.php?url="


def shorten(url: str) -> str:
    if not settings.shorten_links or not url:
        return url
    try:
        req = urllib.request.Request(
            _ENDPOINT + urllib.parse.quote(url, safe=""),
            headers={"User-Agent": "golazo-2026"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:  # noqa: S310
            short = resp.read().decode("utf-8", "ignore").strip()
        if short.startswith("http"):
            return short
        log.warning("tinyurl returned unexpected body: %r", short[:80])
    except Exception:  # noqa: BLE001 — never let shortening break the flow
        log.warning("tinyurl shorten failed; using full URL", exc_info=True)
    return url
