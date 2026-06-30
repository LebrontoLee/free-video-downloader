"""
Authentication module — password hashing, JWT tokens, FastAPI auth dependency.

Uses ONLY Python stdlib:
  - PBKDF2-SHA256 with 600,000 iterations for password hashing (OWASP 2025)
  - HMAC-SHA256 for JSON Web Tokens
  - secrets.compare_digest for timing-safe comparison
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request

from db import get_db

# ─── Config ───────────────────────────────────────────────────────────────────

# JWT secret: auto-generated per-process if not set explicitly.
# For production, set JWT_SECRET in .env so tokens survive server restarts.
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_EXPIRY_HOURS = 168  # 7 days

# ─── Password Hashing ─────────────────────────────────────────────────────────


def hash_password(password: str) -> "tuple[str, str]":
    """Hash a password with a random salt using PBKDF2-SHA256.

    Returns (password_hash_hex, salt_hex).
    Uses 600,000 iterations per OWASP 2025 recommendations.
    """
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 600_000
    )
    return dk.hex(), salt


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """Verify a password against a stored hash + salt.

    Uses secrets.compare_digest for constant-time comparison to prevent
    timing side-channel attacks.
    """
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt_hex.encode("utf-8"), 600_000
    )
    return secrets.compare_digest(dk.hex(), hash_hex)


# ─── JWT (Stdlib-only Implementation) ─────────────────────────────────────────


def _b64url_encode(data: bytes) -> str:
    """Base64url-encode bytes without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Base64url-decode a string (with optional padding)."""
    # Add padding back if needed
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_jwt(user_id: int, email: str) -> str:
    """Create a signed JWT token for the given user.

    Token structure: header.payload.signature
      - header:  {"alg":"HS256","typ":"JWT"}
      - payload: {"sub":<user_id>,"email":<email>,"iat":<issued>,"exp":<expires>}
      - signature: HMAC-SHA256(header.payload, JWT_SECRET)
    """
    header = _b64url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
    )
    now = int(time.time())
    payload = _b64url_encode(
        json.dumps(
            {
                "sub": user_id,
                "email": email,
                "iat": now,
                "exp": now + JWT_EXPIRY_HOURS * 3600,
            },
            separators=(",", ":"),
        ).encode()
    )

    signing_input = f"{header}.{payload}"
    sig = hmac.new(
        JWT_SECRET.encode("utf-8"), signing_input.encode("utf-8"), "sha256"
    ).digest()
    signature = _b64url_encode(sig)

    return f"{signing_input}.{signature}"


def verify_jwt(token: str) -> Optional[dict]:
    """Verify a JWT token and return its payload if valid.

    Returns None if the token is invalid, expired, or tampered with.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}"

        # Verify signature
        expected_sig = hmac.new(
            JWT_SECRET.encode("utf-8"), signing_input.encode("utf-8"), "sha256"
        ).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64))

        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return None


# ─── FastAPI Auth Dependency ───────────────────────────────────────────────────


async def get_current_user(request: Request) -> Optional[dict]:
    """FastAPI dependency: extract and validate the current user from Bearer token.

    Returns a user dict with keys: id, email, is_pro, pro_expires_at
    Returns None if no valid token is provided (anonymous user).

    Usage:
        @app.get("/protected")
        async def protected_route(user = Depends(get_current_user)):
            if user is None:
                raise HTTPException(status_code=401)
            ...
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    claims = verify_jwt(token)
    if claims is None:
        return None

    # Load user from database
    db = get_db()
    cursor = db.execute(
        "SELECT id, email, is_pro, pro_expires_at FROM users WHERE id = ?",
        (claims["sub"],),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    user = dict(row)

    # Check if PRO subscription has expired server-side
    if user["is_pro"] and user["pro_expires_at"]:
        expires = user["pro_expires_at"]
        # Handle both ISO format and timezone awareness
        now_iso = datetime.now(timezone.utc).isoformat()
        if expires < now_iso:
            user["is_pro"] = 0
            # Update database to reflect expiration
            db.execute(
                "UPDATE users SET is_pro = 0 WHERE id = ?", (user["id"],)
            )
            db.commit()

    return user


async def require_auth(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """FastAPI dependency: require a valid user token. Raises 401 if not logged in."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


# ─── Rate Limiting (Simple In-Memory) ──────────────────────────────────────────

# Per-IP rate limit: max attempts in a sliding window
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_MAX = 5       # max attempts per window
RATE_LIMIT_WINDOW = 60   # seconds


def check_rate_limit(ip: str) -> bool:
    """Check if an IP has exceeded the rate limit.

    Returns True if the request is allowed, False if rate limited.
    Cleans up old entries automatically.
    """
    now = time.time()
    if ip not in _rate_limit_store:
        _rate_limit_store[ip] = []

    # Remove entries outside the window
    _rate_limit_store[ip] = [
        t for t in _rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return False

    _rate_limit_store[ip].append(now)
    return True
