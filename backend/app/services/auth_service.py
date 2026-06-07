"""Password hashing with PBKDF2-HMAC-SHA256 (Python stdlib — deliberately
no bcrypt/passlib dependency so the fleet venvs stay lean).

Stored format:  pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ITERATIONS = 240_000
_ALGO = "pbkdf2_sha256"


def hash_password(plain: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(plain: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != _ALGO:
            return False
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(),
                                 bytes.fromhex(salt_hex), int(iters))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk.hex(), hash_hex)


def validate_password(plain: str) -> str | None:
    """Return an error message if the password is too weak, else None."""
    if len(plain) < 8:
        return "Password must be at least 8 characters."
    if plain.isdigit() or plain.isalpha():
        return "Use a mix of letters and numbers."
    return None
