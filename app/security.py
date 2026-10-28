"""Password hashing and signed session tokens, using only the standard library.

Tokens are stateless (an HMAC-signed JSON payload), so any serverless instance can verify
them as long as every instance shares the same ``SECRET_KEY``.
"""

import base64
import hashlib
import hmac
import json
import os
import time

PBKDF2_ITERATIONS = 120_000


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), _b64decode(salt), int(iterations))
        return hmac.compare_digest(candidate, _b64decode(digest))
    except (ValueError, TypeError):
        return False


def create_token(claims: dict, secret: str, ttl_seconds: int) -> str:
    payload = json.dumps({**claims, "exp": int(time.time()) + ttl_seconds}, separators=(",", ":")).encode()
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return f"{_b64encode(payload)}.{_b64encode(signature)}"


def decode_token(token: str, secret: str) -> dict | None:
    """Return the token's claims, or None if it is malformed, tampered with or expired."""
    try:
        payload_part, signature_part = token.split(".")
        payload = _b64decode(payload_part)
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(signature_part)):
            return None
        claims = json.loads(payload)
    except (ValueError, TypeError):
        return None
    if not isinstance(claims, dict) or claims.get("exp", 0) < time.time():
        return None
    return claims
